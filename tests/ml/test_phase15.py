import pytest
import time
from ml.macro.macro_features import MacroCorrelator
from ml.macro.event_processor import EventProcessor, EconomicEvent
from ml.options.gamma_exposure import GammaExposure
from ml.toxicity.vpin_estimator import VPINEstimator

def test_macro_correlation():
    mc = MacroCorrelator(window=5)
    mc.update("BTC", 100)
    mc.update("DXY", 50)
    # Need more data for correlation
    for i in range(10):
        mc.update("BTC", 100 + i)
        mc.update("DXY", 50 - i)
    corr = mc.compute_correlation("BTC", "DXY")
    assert corr != 0.0

def test_event_risk_reduction():
    ep = EventProcessor()
    future_time = int(time.time()) + 3600 # 1 hour from now
    ep.ingest_events([{"name": "FOMC", "impact": "HIGH", "time": future_time}])

    adj = ep.get_risk_adjustment(int(time.time()), lookahead_hours=2)
    assert adj == 0.1 # Should reduce risk

def test_gamma_exposure():
    ge = GammaExposure()
    ge.update_oi(50000, 1000)
    ge.update_oi(60000, 5000)
    res = ge.calculate_net_gex(55000)
    assert "max_pain" in res
    assert res["max_pain"] == 60000

def test_vpin_estimation():
    vp = VPINEstimator(bucket_size=100)
    # Fill bucket with buys only -> High VPIN
    for _ in range(100):
        v = vp.update_trade(1.0, True)
    # Bucket full
    v = vp.update_trade(1.0, True)
    assert v > 0.9 # Should be high toxicity
    assert vp.is_toxic()
