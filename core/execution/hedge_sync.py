from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
import logging

logger = logging.getLogger("golden_bot.exec.hedge_sync")

@dataclass
class HedgePosition:
    long_qty: float = 0.0
    long_price: Optional[float] = None
    short_qty: float = 0.0
    short_price: Optional[float] = None

class HedgeModeTracker:
    def __init__(self):
        self._positions: Dict[str, HedgePosition] = {}

    def sync(self, symbol: str, positions: Dict[str, Dict]) -> None:
        long = positions.get("long", {})
        short = positions.get("short", {})
        self._positions[symbol] = HedgePosition(
            long_qty=long.get("positionAmt", 0.0),
            long_price=long.get("entryPrice"),
            short_qty=short.get("positionAmt", 0.0),
            short_price=short.get("entryPrice")
        )

    def get_net_exposure(self, symbol: str) -> float:
        pos = self._positions.get(symbol, HedgePosition())
        return pos.long_qty - pos.short_qty
