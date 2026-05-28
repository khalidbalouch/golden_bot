import pytest
import numpy as np
import pandas as pd
from ml.drift_monitor import DriftMonitor

def test_psi_stable():
    dm = DriftMonitor(psi_threshold=0.2)
    ref = pd.DataFrame(np.random.randn(500, 3), columns=["a","b","c"])
    dm.set_reference(ref)
    curr = ref + np.random.randn(100, 3) * 0.1
    psi = dm.compute_psi(curr)
    assert all(v < 0.2 for v in psi.values())

def test_concept_drift():
    dm = DriftMonitor(window=100)
    stable = np.random.randn(200)
    assert not dm.detect_concept_drift(stable)
    shifted = np.concatenate([np.zeros(150), np.ones(50) * 5])
    assert dm.detect_concept_drift(shifted)
