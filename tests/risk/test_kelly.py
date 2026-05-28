import pytest
from core.position_sizer import PositionSizer

def test_kelly_bounded():
    sizer = PositionSizer(fractional_coeff=0.25, max_position_pct=0.20)
    size = sizer.compute(equity=10000, stop_distance=100, confidence=0.6, regime="CHOP")
    assert 0 <= size <= 10000 * 0.20

def test_high_vol_reduces_size():
    sizer = PositionSizer()
    sizer.update_volatility(0.05)
    size_high = sizer.compute(10000, 100, 0.6, "CHOP")
    sizer.update_volatility(0.01)
    size_low = sizer.compute(10000, 100, 0.6, "CHOP")
    assert size_high < size_low
