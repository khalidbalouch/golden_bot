import pytest
import pandas as pd
import numpy as np
from core.feature_store import FeatureStore, FeatureSpec

def test_pit_correctness(tmp_path):
    store = FeatureStore(storage_path=str(tmp_path))
    candles = pd.DataFrame({"timestamp": [1,2,3,4,5], "close": [1.0, 1.1, 1.05, 1.2, 1.15]})
    specs = [FeatureSpec("ema", lambda df: df["close"].rolling(2).mean(), window_size=2)]
    feat = store.compute_features(candles, specs)
    store.register_version("v1", specs)
    snap = store.get_point_in_time_snapshot("TEST", 3, ["timestamp","close","ema"])
    assert snap["timestamp"] == 3
    assert snap["close"] == 1.05
    assert np.isclose(snap["ema"], 1.075, rtol=1e-3)
