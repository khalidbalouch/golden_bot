from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger("golden_bot.ml.microstructure")

class MicrostructureFeatures:
    """Streaming orderflow & microstructure alpha (WS-only, zero REST)."""
    def __init__(self, window_size: int = 100):
        self.win = window_size
        self._trade_buf: List[dict] = []
        self._ob_snapshot: Optional[dict] = None

    def push_trade(self, price: float, qty: float, is_buy: bool) -> None:
        self._trade_buf.append({"p": price, "q": qty, "buy": is_buy})
        if len(self._trade_buf) > self.win * 2: self._trade_buf = self._trade_buf[-self.win:]

    def push_orderbook(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]], depth: int = 5) -> None:
        self._ob_snapshot = {
            "bid_vol": sum(b[1] for b in bids[:depth]),
            "ask_vol": sum(a[1] for a in asks[:depth]),
            "mid": (bids[0][0] + asks[0][0]) / 2,
            "spread": asks[0][0] - bids[0][0]
        }

    def compute_all(self) -> Dict[str, float]:
        if not self._trade_buf or not self._ob_snapshot: return {}
        trades = pd.DataFrame(self._trade_buf[-self.win:])
        ob = self._ob_snapshot

        # CVD
        trades["delta"] = np.where(trades["buy"], trades["q"], -trades["q"])
        cvd = trades["delta"].cumsum().iloc[-1]
        cvd_slope = trades["delta"].rolling(20).mean().iloc[-1]

        # Orderbook Imbalance
        ob_imb = (ob["bid_vol"] - ob["ask_vol"]) / (ob["bid_vol"] + ob["ask_vol"] + 1e-9)

        # Spread Dynamics
        spread_bps = (ob["spread"] / ob["mid"]) * 10000

        # Trade Imbalance
        buy_vol = trades[trades["buy"]]["q"].sum()
        sell_vol = trades[~trades["buy"]]["q"].sum()
        vol_imb = (buy_vol - sell_vol) / (buy_vol + sell_vol + 1e-9)

        return {
            "cvd": cvd, "cvd_slope": cvd_slope,
            "ob_imbalance": ob_imb, "spread_bps": spread_bps, "vol_imbalance": vol_imb
        }
