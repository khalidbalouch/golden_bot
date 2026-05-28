from __future__ import annotations
import asyncio
import logging
import time
from typing import Dict, Optional
from ml.features_microstructure import MicrostructureFeatures
from ml.features_derivatives import DerivativeFeatures
from core.ws_manager import BinanceWSManager
from core.feature_store import FeatureStore, FeatureSpec

logger = logging.getLogger("golden_bot.ml.feature_pipeline")

class FeaturePipeline:
    """Async WS-driven feature computation engine."""
    def __init__(self, ws_manager: BinanceWSManager, symbol: str = "BTCUSDT"):
        self.ws = ws_manager
        self.symbol = symbol
        self.micro = MicrostructureFeatures()
        self.deriv = DerivativeFeatures()
        self.store = FeatureStore()
        self._latest: Dict[str, float] = {}
        self._running = False
        self._register_ws_handlers()

    def _register_ws_handlers(self) -> None:
        self.ws.register_handler("trade", self._on_trade)
        self.ws.register_handler("depthUpdate", self._on_depth)
        self.ws.register_handler("markPrice", self._on_mark_price)
        self.ws.register_handler("fundingRate", self._on_funding)

    def _on_trade(self, data: dict) -> None:
        self.micro.push_trade(float(data.get("p", 0)), float(data.get("q", 0)), not data.get("m", False))
        self._compute_and_store()

    def _on_depth(self, data: dict) -> None:
        bids = [(float(b[0]), float(b[1])) for b in data.get("b", [])]
        asks = [(float(a[0]), float(a[1])) for a in data.get("a", [])]
        if bids and asks: self.micro.push_orderbook(bids, asks)

    def _on_mark_price(self, data: dict) -> None:
        self._latest["mark_price"] = float(data.get("p", 0))
        self._compute_and_store()

    def _on_funding(self, data: dict) -> None:
        self.deriv.push_funding(float(data.get("r", 0)))
        self.deriv.push_oi(float(data.get("i", 0)))
        self._compute_and_store()

    def _compute_and_store(self) -> None:
        try:
            feats = {}
            micro_feats = self.micro.compute_all()
            deriv_feats = self.deriv.compute_all(self._latest.get("mark_price", 0))
            feats.update(micro_feats)
            feats.update(deriv_feats)
            self._latest.update(feats)
            self._latest["ts"] = time.time()
        except Exception as e:
            logger.debug(f"Feature compute skipped: {e}")

    def get_latest(self) -> Dict[str, float]: return dict(self._latest)

    async def run_validation(self) -> None:
        self._running = True
        logger.info(f"🧠 Feature pipeline active for {self.symbol} (WS-driven)")
        self.store.register_version("phase4_v1", [
            FeatureSpec("cvd", lambda df: df["cvd"], 100),
            FeatureSpec("ob_imbalance", lambda df: df["ob_imbalance"], 100),
            FeatureSpec("funding_alpha_bps", lambda df: df["funding_alpha_bps"], 24)
        ])

    async def stop(self) -> None: self._running = False
