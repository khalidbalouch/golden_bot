from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List

logger = logging.getLogger("golden_bot.vol_estimator")

class VolatilityEstimator:
    """Realized vol, EMA smoothing, regime-adjusted forecasting."""
    def __init__(self, ema_span: int = 20, annualization_factor: float = 16.0): # 16 for 15m
        self.span = ema_span
        self.ann = annualization_factor
        self._vol_history: List[float] = []

    def update(self, prices: pd.Series) -> float:
        returns = prices.pct_change().dropna()
        realized = returns.std() * self.ann
        ema_vol = pd.Series(self._vol_history + [realized]).ewm(span=self.span).mean().iloc[-1]
        self._vol_history.append(realized)
        if len(self._vol_history) > 100: self._vol_history.pop(0)
        return float(ema_vol)

    def forecast_next(self) -> float:
        if not self._vol_history: return 0.02
        return self._vol_history[-1] * 1.05 # Simple mean-reversion bump for safety

    def classify_regime(self, current_vol: float, median_vol: float) -> str:
        ratio = current_vol / (median_vol + 1e-9)
        if ratio > 1.5: return "HIGHVOL"
        if ratio < 0.8: return "TREND"
        return "CHOP"
