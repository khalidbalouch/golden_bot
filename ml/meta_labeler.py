from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional
import xgboost as xgb

logger = logging.getLogger("golden_bot.ml.meta_labeler")

class MetaLabeler:
    """Lightweight classifier predicting trade profitability after fees & slippage."""
    def __init__(self, max_depth: int = 3, n_estimators: int = 100, threshold: float = 0.6):
        self.threshold = threshold
        self.model = xgb.XGBClassifier(max_depth=max_depth, n_estimators=n_estimators, eval_metric="logloss")
        self._fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "MetaLabeler":
        self.model.fit(X, y, verbose=False)
        self._fitted = True
        logger.info(f"✅ MetaLabeler trained: {len(X)} examples, threshold={self.threshold}")
        return self

    def predict_trade_viability(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted: raise RuntimeError("MetaLabeler not fitted")
        probs = self.model.predict_proba(X)[:, 1]
        return pd.DataFrame({"probability": probs, "recommendation": np.where(probs >= self.threshold, "take", "skip")})

    def get_feature_contributions(self, X: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(self.model.feature_importances_, index=X.columns, columns=["importance"])
