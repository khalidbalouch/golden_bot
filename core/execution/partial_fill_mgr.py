from __future__ import annotations
import logging
from typing import Dict, Optional
from core.execution.state_machine import OrderStateMachine, OrderState

logger = logging.getLogger("golden_bot.exec.partial_fill_mgr")

class PartialFillReconciler:
    def __init__(self, tolerance_pct: float = 0.01):
        self._tolerance = tolerance_pct

    def reconcile(self, order_id: str, state_machine: OrderStateMachine, internal_filled: float, exchange_filled: float, quantity: float) -> None:
        diff_pct = abs(internal_filled - exchange_filled) / max(quantity, 1e-9)
        if diff_pct > self._tolerance:
            logger.warning(f"⚠️ Fill drift for {order_id}: internal={internal_filled}, exchange={exchange_filled}, diff={diff_pct:.4f}")
        remaining = quantity - exchange_filled
        if state_machine.state == OrderState.PARTIALLY_FILLED and remaining < quantity * 0.01:
            state_machine.transition(OrderState.FILLED, {"reason": "dust_threshold_reached"})
