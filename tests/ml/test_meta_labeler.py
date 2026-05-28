import pytest
import pandas as pd
import numpy as np
from ml.meta_labeler import MetaLabeler

def test_meta_viability():
    ml = MetaLabeler()
    X = pd.DataFrame(np.random.randn(200, 4))
    y = (X.sum(axis=1) > 0).astype(int)
    ml.fit(X, y)
    res = ml.predict_trade_viability(X.head(20))
    assert len(res) == 20
    assert "probability" in res.columns
    assert res["probability"].between(0, 1).all()
