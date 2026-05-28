from __future__ import annotations
import asyncio
import logging
from typing import Dict, Optional
from ml.macro.macro_features import MacroCorrelator
from ml.macro.event_processor import EventProcessor
from ml.options.vol_surface import VolatilitySurface
from ml.options.gamma_exposure import GammaExposure
from ml.toxicity.vpin_estimator import VPINEstimator

logger = logging.getLogger("golden_bot.macro_orchestrator")

class MacroOrchestrator:
    """Integrates Macro, Options, and Toxicity signals."""
    def __init__(self):
        self.correlator = MacroCorrelator()
        self.event_proc = EventProcessor()
        self.vol_surface = VolatilitySurface()
        self.gex = GammaExposure()
        self.vpin = VPINEstimator(bucket_size=1000000) # 1M volume bucket

    def process_tick(self, symbol: str, price: float, volume: float, is_buy: bool, time_utc: int) -> Dict:
        # 1. Update Macro
        self.correlator.update(symbol, price)
        self.correlator.update("DXY", 104.0 + (price/10000)) # Simulated DXY correlation

        # 2. Update Toxicity
        current_vpin = self.vpin.update_trade(volume, is_buy)

        # 3. Check Risk Environment
        risk_mult = self.event_proc.get_risk_adjustment(time_utc)

        return {
            "vpin": current_vpin,
            "toxicity_alert": self.vpin.is_toxic(),
            "risk_multiplier": risk_mult,
            "dxy_corr": self.correlator.compute_correlation(symbol, "DXY")
        }

    def get_options_bias(self, symbol: str, spot: float) -> Dict:
        # Simulated GEX calc
        return self.gex.calculate_net_gex(spot)
