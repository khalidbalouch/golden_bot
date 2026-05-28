import pytest
import pandas as pd
import numpy as np
from core.data_intelligence.synthetic_generator import SyntheticMarketGenerator
from core.data_intelligence.regime_balancer import RegimeBalancer
from core.data_intelligence.lineage_tracker import DataLineageTracker
from core.data_intelligence.anomaly_detector import MultiDimensionalAnomalyDetector
from core.data_intelligence.drift_explainer import DriftExplainer

def test_synthetic_generation():
    base = pd.DataFrame({"close":np.random.randn(100), "volume":np.random.randint(10,100,100)})
    regs = pd.Series(["TREND"]*50 + ["CHOP"]*50)
    gen = SyntheticMarketGenerator(base, regs)
    gen.train_generative_model()
    out = gen.generate_synthetic_dataset(200, {"TREND":0.5, "CHOP":0.5})
    assert len(out) == 200
    assert set(out["regime"]) == {"TREND", "CHOP"}

def test_regime_balancing():
    bal = RegimeBalancer({"A":0.7, "B":0.3})
    orig = pd.DataFrame({"regime":["A"]*80 + ["B"]*20})
    bal = bal.balance_dataset(orig, "regime")
    assert len(bal) == 100
    assert abs(bal["regime"].value_counts(normalize=True)["A"] - 0.7) < 0.1

def test_lineage_tracker(tmp_path):
    tr = DataLineageTracker(path=str(tmp_path))
    tr.record_step("step1", ["in1"], ["out1"], {"a":1}, "hash1")
    tr.record_step("step2", ["out1"], ["out2"], {"b":2}, "hash2")
    path = tr.query_lineage("out2")
    assert len(path.nodes) == 2
    assert path.nodes[0].step_id == "step2"

def test_anomaly_and_drift():
    train = pd.DataFrame(np.random.randn(100,3), columns=["x","y","z"])
    det = MultiDimensionalAnomalyDetector()
    det.fit(train)
    reports = det.detect_anomalies(train.head(10))
    assert isinstance(reports, list)
    exp = DriftExplainer(train)
    shifted = train.copy()
    shifted["x"] *= 3.0
    drifts = exp.explain_drift(shifted)
    assert len(drifts) > 0
