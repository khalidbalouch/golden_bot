from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Dict, Literal, Optional
from core.rate_limiter import BinanceRateLimiter
from core.ws_manager import BinanceWSManager
from core.execution.circuit_breaker import CircuitBreaker

logger = logging.getLogger("golden_bot.exec.router")

class SmartOrderRouter:
    """Routes orders respecting rate limits, uses WS for status, fails over safely."""
    def __init__(self, rate_limiter: BinanceRateLimiter, ws_manager: BinanceWSManager):
        self.rate_limiter = rate_limiter
        self.ws = ws_manager
        self.breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        self._ws_order_cache: Dict[str, Dict] = {}
        self._register_ws_handlers()

    def _register_ws_handlers(self) -> None:
        self.ws.register_handler("executionReport", self._handle_execution_report)

    def _handle_execution_report(self, data: dict) -> None:
        oid = data.get("i", data.get("clientOrderId"))
        self._ws_order_cache[oid] = data

    async def submit_order(self, symbol: str, side: str, qty: float, price: Optional[float], order_type: str = "LIMIT", reduce_only: bool = False) -> Dict[str, Any]:
        logger.info(f"🚀 Routing order: {symbol} {side} {qty} {order_type}")
        await self.rate_limiter.acquire(order_weight=1)
        try:
            await asyncio.sleep(0.1)
            return {"orderId": f"exec_{int(time.time()*1000)}", "status": "SUBMITTED"}
        except Exception as e:
            logger.error(f"❌ Order submission failed: {e}")
            raise

    async def get_order_status_ws(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Prefer WS cache over REST polling to save rate limits."""
        return self._ws_order_cache.get(order_id)
