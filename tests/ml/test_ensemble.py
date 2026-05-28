import pytest
import numpy as np
import pandas as pd
from ml.ensemble_manager import StackingEnsemble, DynamicWeighter

def test_stacking_fit_predict():
    X = pd.DataFrame(np.random.randn(100, 5), columns=["f1","f2","f3","f4","f5"])
    y = (X["f1"] > 0).astype(int)
    ens = StackingEnsemble(n_folds=3)
    ens.fit(X, y)
    probs = ens.predict_proba(X.head(10))
    assert probs.shape == (10, 1)
    assert np.all((probs >= 0) & (probs <= 1))

def test_dynamic_weighter():
    dw = DynamicWeighter()
    dw.update({"xgb": 0.65, "lgb": 0.60})
    w = dw.compute_weights()
    assert abs(sum(w.values()) - 1.0) < 1e-6
