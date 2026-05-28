import pytest
import pandas as pd
import numpy as np
from utils.walk_forward import WalkForwardValidator, DataFold

def test_fold_generation():
    data = pd.DataFrame(np.random.randn(500, 3), columns=["a","b","c"])
    wf = WalkForwardValidator(train_months=1, test_months=1, step_months=1)
    folds = wf.generate_folds(data)
    assert len(folds) > 0
    assert folds[0].train_end == folds[0].test_start
    for f in folds:
        assert f.train_end <= f.test_end
