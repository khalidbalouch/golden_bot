from __future__ import annotations
import logging
import numpy as np
from typing import Optional
from core.trade_manager import Trade

logger = logging.getLogger("golden_bot.trailing_stop")

class TrailingStop:
    """Chandelier + ATR-based volatility-adaptive trailing."""
    def __init__(self, atr_multiplier: float = 2.0, min_atr: float = 0.001):
        self.atr_mult = atr_multiplier
        self.min_atr = min_atr

    def compute(self, trade: Trade, current_price: float, state: Dict) -> Optional[float]:
        extreme = state.get("extreme_price", trade.entry_price)
        atr = max(self.min_atr, abs(extreme - trade.entry_price) * 0.5) # Simplified ATR proxy

        if trade.direction == "LONG":
            trail = extreme - (self.atr_mult * atr)
            # Never move below original SL or previous trail
            trail = max(trail, trade.sl_price)
        else:
            trail = extreme + (self.atr_mult * atr)
            trail = min(trail, trade.sl_price)

        # Activate trailing only after TP1 hit or breakeven
        if not trade.trailing_active and trade.pnl_pct(current_price) > 0.5:
            trade.trailing_active = True
            trade.breakeven_moved = True

        return trail if trade.trailing_active else None
