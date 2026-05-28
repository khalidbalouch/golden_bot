import pytest
from core.trade_manager import Trade
from utils.trailing_stop import TrailingStop

def test_trailing_never_worsens_sl():
    trade = Trade("t1", "BTCUSDT", "LONG", 50000.0, 49000.0, 51500.0, 52000.0, 1.0, 1.0)
    ts = TrailingStop(atr_multiplier=2.0)
    state = {"extreme_price": 51000.0}
    trail = ts.compute(trade, 51000.0, state)
    assert trail >= trade.sl_price
