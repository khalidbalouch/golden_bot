from __future__ import annotations
import asyncio
import logging
import os
from typing import Any, Dict, Optional
from core.rate_limiter import BinanceRateLimiter
from core.ws_manager import BinanceWSManager
from core.execution.state_machine import OrderStateMachine, OrderState
from core.execution.router import SmartOrderRouter
from core.execution.partial_fill_mgr import PartialFillReconciler
from core.execution.reduce_only import ReduceOnlyEnforcer
from core.execution.hedge_sync import HedgeModeTracker
from core.security import AuditLogger, AuditAction

logger = logging.getLogger("golden_bot.execution_engine")

class ExecutionEngine:
    def __init__(self, audit: AuditLogger):
        self.audit = audit
        self.rate_limiter = BinanceRateLimiter()
        self.ws = BinanceWSManager(api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET"))
        self.router = SmartOrderRouter(self.rate_limiter, self.ws)
        self.reconciler = PartialFillReconciler()
        self.reduce_only = ReduceOnlyEnforcer()
        self.hedge_sync = HedgeModeTracker()
        self._order_states: Dict[str, OrderStateMachine] = {}
        self._running = False

    async def start(self) -> None:
        await self.ws.start(streams=["!ticker@arr", "executionReport"], handlers={"executionReport": [self._on_ws_fill]})
        self._running = True
        logger.info("🟢 Execution Engine started (WS-first, rate-limited)")

    async def place_order(self, order_id: str, symbol: str, side: str, qty: float, price: Optional[float]) -> Dict[str, Any]:
        if not self.reduce_only.validate(symbol, side, qty):
            raise ValueError("Reduce-only violation")
        self._order_states[order_id] = OrderStateMachine(order_id)
        self.audit.log(AuditAction.TRADE_EXECUTION, None, "engine", "127.0.0.1", "success", f"Order {order_id} submitted")
        result = await self.router.submit_order(symbol, side, qty, price)
        self._order_states[order_id].transition(OrderState.SUBMITTED, {"exchange_id": result.get("orderId")})
        return result

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        state = self._order_states.get(order_id)
        if state and state.state in (OrderState.FILLED, OrderState.CANCELLED):
            return {"status": "ALREADY_CLOSED"}
        self.audit.log(AuditAction.TRADE_EXECUTION, None, "engine", "127.0.0.1", "success", f"Order {order_id} cancel requested")
        return {"status": "CANCELLED"}

    def _on_ws_fill(self, data: dict) -> None:
        oid = data.get("i", "")
        if oid in self._order_states:
            filled = float(data.get("z", 0))
            qty = float(data.get("q", 0))
            status_map = {"NEW": OrderState.SUBMITTED, "PARTIALLY_FILLED": OrderState.PARTIALLY_FILLED, "FILLED": OrderState.FILLED, "CANCELED": OrderState.CANCELLED}
            new_state = status_map.get(data.get("X", ""), None)
            if new_state:
                self._order_states[oid].transition(new_state, {"exec_type": data.get("x")})
            self.reconciler.reconcile(oid, self._order_states[oid], 0.0, filled, qty)

    async def stop(self) -> None:
        self._running = False
        await self.ws.close()
        logger.info("🔴 Execution Engine stopped")
