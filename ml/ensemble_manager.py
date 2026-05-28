from __future__ import annotations
import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import xgboost as xgb
import lightgbm as lgb
from sklearn.base import BaseEstimator, clone
from sklearn.model_selection import KFold

logger = logging.getLogger("golden_bot.ml.ensemble")

class StackingEnsemble(BaseEstimator):
    """Production stacking ensemble: XGBoost + LightGBM base learners + LogisticRegression meta-learner."""
    def __init__(self, n_folds: int = 5, meta_model: Optional[BaseEstimator] = None):
        self.n_folds = n_folds
        self.meta = meta_model
        self.base_models: List[Tuple[str, BaseEstimator]] = [
            ("xgb", xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.05, eval_metric="logloss")),
            ("lgb", lgb.LGBMClassifier(n_estimators=300, max_depth=6, learning_rate=0.05, metric="binary"))
        ]
        self._fitted_bases: List[Tuple[str, BaseEstimator]] = []
        self._meta_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "StackingEnsemble":
        kf = KFold(n_splits=self.n_folds, shuffle=True, random_state=42)
        oof_preds = pd.DataFrame(index=X.index)
        self._fitted_bases = []

        for name, base in self.base_models:
            fold_preds = np.zeros(len(X))
            for train_idx, val_idx in kf.split(X):
                X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
                X_val = X.iloc[val_idx]
                m = clone(base)
                m.fit(X_tr, y_tr, eval_set=[(X_val, y_val.iloc[val_idx])], verbose=False)
                fold_preds[val_idx] = m.predict_proba(X_val)[:, 1]
                if name not in [n for n, _ in self._fitted_bases]:
                    self._fitted_bases.append((name, clone(m)))
            oof_preds[name] = fold_preds

        if self.meta is not None:
            self.meta.fit(oof_preds, y)
            self._meta_fitted = True
        logger.info(f"✅ StackingEnsemble trained on {len(X)} samples, OOF preds computed")
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        base_preds = {}
        for name, model in self._fitted_bases:
            base_preds[name] = model.predict_proba(X)[:, 1]
        base_df = pd.DataFrame(base_preds)
        if self._meta_fitted:
            return self.meta.predict_proba(base_df)
        return base_df.mean(axis=1).values.reshape(-1, 1)

    def get_feature_importance(self) -> Dict[str, float]:
        """Aggregate SHAP/importance across base models."""
        importances = {}
        for name, m in self._fitted_bases:
            if hasattr(m, "feature_importances_"):
                importances[name] = m.feature_importances_.tolist()
        return importances

class DynamicWeighter:
    """Adjusts model weights based on rolling Sharpe & calibration error."""
    def __init__(self, window: int = 50, decay: float = 0.95):
        self.window = window
        self.decay = decay
        self._history: List[Dict[str, float]] = []

    def update(self, model_perf: Dict[str, float]) -> None:
        self._history.append(model_perf)
        if len(self._history) > self.window: self._history.pop(0)

    def compute_weights(self) -> Dict[str, float]:
        if not self._history: return {"xgb": 0.5, "lgb": 0.5}
        recent = self._history[-10:]
        raw = {k: 0.0 for k in recent[0].keys()}
        for h in recent:
            for k, v in h.items():
                raw[k] += v * self.decay ** (len(recent) - recent.index(h))
        total = sum(raw.values()) + 1e-9
        return {k: v/total for k, v in raw.items()}
