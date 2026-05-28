import pytest
from core.trade_manager import Trade
from utils.tp_ladder import TPLadder
from core.exit_engine import ExitAction

def test_tp1_trigger_long():
trade = Trade("t1", "BTCUSDT", "LONG", 50000.0, 49000.0, 51000.0, 52000.0, 1.0, 1.0)
ladder = TPLadder()
actions = ladder.evaluate_triggers(trade, 51500.0)
assert any(a.exit_type == "tp_ladder" for a in actions)
