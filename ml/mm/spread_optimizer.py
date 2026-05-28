from __future__ import annotations
import logging
from typing import Dict, Optional

logger = logging.getLogger("golden_bot.mm.spread")

class SpreadOptimizer:
    """Dynamic spread adjustment based on market regime and fee tier."""
    def __init__(self, base_spread_bps: float = 10.0, min_spread_bps: float = 2.0):
        self.base_spread = base_spread_bps
        self.min_spread = min_spread_bps

    def calculate_adaptive_spread(self, volatility: float, maker_rebate: float, 
                                  regime: str = "CHOP") -> float:
        """
        Increases spread in high vol, decreases in low vol.
        Accounts for maker rebates to ensure positive expectancy.
        """
        # Volatility multiplier
        vol_mult = max(1.0, volatility * 100.0) # e.g. if vol is 0.02, mult is 2.0

        # Regime adjustment
        regime_mult = {"TREND": 1.5, "HIGHVOL": 2.0, "CHOP": 1.0}.get(regime, 1.0)

        # Rebate adjustment (if rebate is high, we can afford tighter spreads)
        rebate_discount = max(0.0, maker_rebate * 50.0) 

        spread = (self.base_spread * vol_mult * regime_mult) - rebate_discount
        return max(spread, self.min_spread)
