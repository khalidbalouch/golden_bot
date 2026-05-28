from __future__ import annotations
import asyncio
import json
import time
from typing import Any, Dict

class MockExchange:
    """Simulates Binance behavior with realistic rate limit responses."""
    def __init__(self):
        self.orders: Dict[str, Any] = {}
        self._call_count = 0

    async def post(self, path: str, payload: dict) -> Dict[str, Any]:
        self._call_count += 1
        headers = {
            "x-mbx-used-weight-1m": str(self._call_count),
            "x-mbx-order-count-1s": "1"
        }
        order_id = f"mock_{int(time.time()*1000)}"
        self.orders[order_id] = {"orderId": order_id, "status": "NEW", **payload}
        return self.orders[order_id], headers

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        return self.orders.get(order_id, {})
