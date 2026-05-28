from __future__ import annotations
import numpy as np

class MarketImpactModel:
    """Square-root impact model: ΔP = b * sqrt(Q/V) * σ"""
    def __init__(self, b: float = 0.1, daily_volume: float = 1e9):
        self.b = b
        self.daily_vol = daily_volume

    def compute(self, price: float, qty: float, volatility_pct: float) -> float:
        vol_ratio = qty / self.daily_vol
        impact = self.b * np.sqrt(vol_ratio) * volatility_pct * price
        return impact
