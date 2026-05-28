from __future__ import annotations
import logging
import asyncio
import time
from typing import Dict, Optional, Callable

logger = logging.getLogger("golden_bot.execution")

class TWAPExecutor:
    """Time-Weighted Average Price execution to minimize market impact."""
    async def execute(self, symbol: str, side: str, total_qty: float, 
                      duration_min: int, executor_fn: Callable, 
                      interval_sec: int = 60) -> Dict:
        slices = duration_min * 60 // interval_sec
        qty_per_slice = total_qty / slices
        filled = 0.0
        vwap = 0.0

        for _ in range(slices):
            res = await executor_fn(symbol, side, qty_per_slice)
            filled += res.get("filled", 0)
            # Update VWAP calculation
            vwap = ((vwap * (filled - res["filled"])) + (res.get("avg_price", 0) * res["filled"])) / (filled + 1e-9)
            await asyncio.sleep(interval_sec)
        return {"total_filled": filled, "vwap": vwap}

class IcebergOrder:
    """Hides large orders by splitting into visible chunks."""
    def __init__(self, visible_qty: float = 0.1):
        self.visible = visible_qty

    def get_chunk(self, remaining: float) -> float:
        return min(self.visible, remaining)
