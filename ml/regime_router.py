from __future__ import annotations
import logging
import numpy as np
from typing import Dict, Optional
from sklearn.mixture import GaussianMixture

logger = logging.getLogger("golden_bot.ml.regime_router")

class RegimeRouter:
    """Routes inference to regime-specific models using HMM-like GMM clustering."""
    def __init__(self, n_regimes: int = 3):
        self.n_regimes = n_regimes
        self._gmm = GaussianMixture(n_components=n_regimes, random_state=42)
        self._regime_models: Dict[int, object] = {}
        self._fitted = False

    def fit_regimes(self, X: pd.DataFrame) -> None:
        self._gmm.fit(X)
        self._fitted = True
        logger.info(f"🌐 RegimeRouter fitted {self.n_regimes} regimes via GMM")

    def predict_regime(self, X: pd.DataFrame) -> np.ndarray:
        if not self._fitted: raise RuntimeError("RegimeRouter not fitted")
        return self._gmm.predict(X)

    def route_predict(self, X: pd.DataFrame, models: Dict[int, object]) -> np.ndarray:
        regimes = self.predict_regime(X)
        preds = np.zeros(len(X))
        for r in range(self.n_regimes):
            mask = regimes == r
            if mask.any() and r in models:
                preds[mask] = models[r].predict_proba(X[mask])[:, 1]
        return preds
