from __future__ import annotations
import logging
import numpy as np
from typing import Optional

logger = logging.getLogger("golden_bot.position_sizer")

class PositionSizer:
    """Fractional Kelly sizing with confidence, regime & volatility modulators."""
    def __init__(self, fractional_coeff: float = 0.25, max_position_pct: float = 0.20,
                 target_volatility: float = 0.02, min_position_usd: float = 10.0):
        self.frac = fractional_coeff
        self.max_pct = max_position_pct
        self.target_vol = target_volatility
        self.min_usd = min_position_usd
        self._realized_vol = 0.02

    def compute(self, equity: float, stop_distance: float, confidence: float, regime: str) -> float:
        if stop_distance <= 0: return 0.0

        # Base fractional Kelly: f = (p*b - q)/b
        win_prob = max(0.3, min(0.9, confidence))
        loss_prob = 1.0 - win_prob
        risk_reward = 1.5 # Assumed TP/SL ratio, dynamically adjustable later
        b = risk_reward
        q = loss_prob
        f_kelly = max(0.0, (win_prob * b - q) / b) * self.frac

        # Modulators
        regime_adj = {"TREND": 1.0, "CHOP": 0.7, "HIGHVOL": 0.5}.get(regime, 0.8)
        vol_adj = min(1.5, max(0.5, self.target_vol / (self._realized_vol + 1e-9)))
        conf_adj = win_prob / 0.65

        raw_size = equity * f_kelly * regime_adj * vol_adj * conf_adj
        position_value = raw_size / (stop_distance / 100.0) # Approximate notional

        # Hard limits
        max_notional = equity * self.max_pct
        notional = min(max(self.min_usd, position_value), max_notional)

        # Convert back to quantity
        qty = notional / 100.0 # Placeholder price normalization
        return max(0.0, qty)

    def update_volatility(self, realized_vol: float) -> None:
        self._realized_vol = max(0.001, realized_vol)
