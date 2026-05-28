from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional
import logging

logger = logging.getLogger("golden_bot.exec.reduce_only")

@dataclass
class PositionState:
    symbol: str
    net_size: float = 0.0
    long_entry_price: Optional[float] = None
    short_entry_price: Optional[float] = None

class ReduceOnlyEnforcer:
    def __init__(self):
        self._positions: dict[str, PositionState] = {}

    def update_position(self, symbol: str, net_size: float, long_price: Optional[float] = None, short_price: Optional[float] = None) -> None:
        self._positions[symbol] = PositionState(symbol, net_size, long_price, short_price)

    def validate(self, symbol: str, side: Literal["BUY", "SELL"], quantity: float) -> bool:
        pos = self._positions.get(symbol, PositionState(symbol))
        if pos.net_size == 0.0: return True
        if pos.net_size > 0 and side == "BUY": return False
        if pos.net_size < 0 and side == "SELL": return False
        if pos.net_size > 0 and side == "SELL" and quantity > pos.net_size:
            logger.warning(f"🛡️ Reduce-only: capping {side} qty from {quantity} to {pos.net_size}")
            return False
        if pos.net_size < 0 and side == "BUY" and quantity > abs(pos.net_size):
            logger.warning(f"🛡️ Reduce-only: capping {side} qty from {quantity} to {abs(pos.net_size)}")
            return False
        return True
