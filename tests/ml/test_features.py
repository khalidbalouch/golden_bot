import pytest
import numpy as np
from ml.features_microstructure import MicrostructureFeatures
from ml.features_derivatives import DerivativeFeatures

def test_microstructure_compute():
    mf = MicrostructureFeatures(window_size=10)
    mf.push_trade(100.0, 1.0, True)
    mf.push_trade(101.0, 0.5, False)
    mf.push_orderbook([(99.9, 5.0), (99.8, 2.0)], [(100.1, 3.0), (100.2, 1.0)])
    res = mf.compute_all()
    assert "cvd" in res and "ob_imbalance" in res
    assert abs(res["ob_imbalance"]) <= 1.0

def test_derivatives_compute():
    df = DerivativeFeatures()
    df.push_funding(0.0001); df.push_funding(0.0002); df.push_funding(0.00015)
    df.push_oi(1000); df.push_oi(1050)
    res = df.compute_all(current_price=100.0, liq_clusters=[105.0, 95.0])
    assert "funding_alpha_bps" in res
    assert "oi_momentum" in res
    assert 0.0 <= res.get("liq_proximity", 0) <= 1.0
