import pytest
from core.execution.state_machine import OrderStateMachine, OrderState

def test_valid_transitions():
    sm = OrderStateMachine("oid1")
    assert sm.state == OrderState.PENDING
    assert sm.transition(OrderState.SUBMITTED)
    assert sm.transition(OrderState.PARTIALLY_FILLED)
    assert sm.transition(OrderState.FILLED)
    assert len(sm.get_history()) == 3

def test_invalid_transition():
    sm = OrderStateMachine("oid2")
    assert sm.state == OrderState.PENDING
    assert not sm.transition(OrderState.FILLED)
