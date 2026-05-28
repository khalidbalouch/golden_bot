from __future__ import annotations
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("golden_bot.exec.state_machine")

class OrderState(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

VALID_TRANSITIONS = {
    OrderState.PENDING: {OrderState.SUBMITTED, OrderState.CANCELLED},
    OrderState.SUBMITTED: {OrderState.PARTIALLY_FILLED, OrderState.FILLED, OrderState.CANCELLED, OrderState.REJECTED, OrderState.EXPIRED},
    OrderState.PARTIALLY_FILLED: {OrderState.FILLED, OrderState.CANCELLED},
    OrderState.FILLED: set(),
    OrderState.CANCELLED: set(),
    OrderState.REJECTED: set(),
    OrderState.EXPIRED: set()
}

@dataclass
class StateTransition:
    from_state: OrderState
    to_state: OrderState
    timestamp: float
    meta: Dict[str, Any] = field(default_factory=dict)

class OrderStateMachine:
    def __init__(self, order_id: str, initial_state: OrderState = OrderState.PENDING):
        self.order_id = order_id
        self._state = initial_state
        self._history: List[StateTransition] = []

    @property
    def state(self) -> OrderState: return self._state

    def transition(self, new_state: OrderState, meta: Optional[Dict[str, Any]] = None) -> bool:
        if new_state not in VALID_TRANSITIONS[self._state]:
            logger.warning(f"⛔ Invalid transition {self._state.value} -> {new_state.value} for {self.order_id}")
            return False
        t = StateTransition(self._state, new_state, time.time(), meta or {})
        self._history.append(t)
        self._state = new_state
        logger.debug(f"🔄 {self.order_id}: {t.from_state.value} -> {t.to_state.value}")
        return True

    def get_history(self) -> List[StateTransition]: return self._history
