import pytest
from core.portfolio_allocator import PortfolioAllocator

def test_equal_weights():
    alloc = PortfolioAllocator(mode="equal")
    signals = [{"symbol": "A"}, {"symbol": "B"}, {"symbol": "C"}]
    weights = alloc.compute_weights(signals, {})
    assert abs(sum(weights.values()) - 1.0) < 1e-6
    assert all(abs(w - 0.333) < 0.01 for w in weights.values())

def test_max_weight_cap():
    alloc = PortfolioAllocator(mode="conviction", max_single_weight=0.40)
    signals = [{"symbol": "A", "confidence": 0.9, "ev": 0.8}, {"symbol": "B", "confidence": 0.4, "ev": 0.3}]
    weights = alloc.compute_weights(signals, {})
    assert all(w <= 0.40 for w in weights.values())
