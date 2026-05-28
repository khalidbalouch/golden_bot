import pytest
from core.execution.state_machine import OrderStateMachine, OrderState
from core.execution.partial_fill_mgr import PartialFillReconciler

def test_dust_threshold():
    rec = PartialFillReconciler(tolerance_pct=0.005)
    sm = OrderStateMachine("test")
    sm.transition(OrderState.SUBMITTED)
    rec.reconcile("test", sm, 0.0, 0.999, 1.0)
    assert sm.state == OrderState.PARTIALLY_FILLED
