import pytest
import time
from core.trade_manager import Trade
from utils.time_decay import TimeDecayExit

def test_max_duration_exit():
trade = Trade("t1", "BTCUSDT", "LONG", 50000.0, 49000.0, 51000.0, None, 1.0, 1.0)
trade.open_time = time.time() - 10000 # 10000s ago
td = TimeDecayExit(max_duration_min=60)
res = td.evaluate(trade, 50000.0)
assert res is not None and "max_duration" in res.reason
