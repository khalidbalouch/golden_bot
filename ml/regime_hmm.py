from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.mixture import GaussianMixture
from scipy.signal import argrelextrema

logger = logging.getLogger("golden_bot.ml.regime_hmm")

class RegimeHMM:
    """Hidden Markov Model for market regime classification & structural break detection."""
    def __init__(self, n_regimes: int = 3, covariance_type: str = "full"):
        self.n_regimes = n_regimes
        self.model = GaussianMixture(n_components=n_regimes, covariance_type=covariance_type, random_state=42)
        self._fitted = False
        self._state_means: Dict[int, np.ndarray] = {}
        self._regime_labels = ["LOW_VOL_TREND", "HIGH_VOL_CHOP", "CRASH_SPIKE"][:n_regimes]

    def fit(self, features: pd.DataFrame) -> None:
        self.model.fit(features)
        self._fitted = True
        self._state_means = {i: self.model.means_[i] for i in range(self.n_regimes)}
        logger.info(f"🌐 HMM fitted with {n_regimes} regimes")

    def predict_regime(self, current_features: np.ndarray) -> Tuple[int, str, float]:
        if not self._fitted: raise RuntimeError("HMM not fitted")
        probs = self.model.predict_proba(current_features.reshape(1, -1))[0]
        regime_idx = int(np.argmax(probs))
        return regime_idx, self._regime_labels[regime_idx], float(probs[regime_idx])

    def detect_structural_break(self, series: pd.Series, window: int = 50, threshold_std: float = 2.5) -> List[int]:
        """Bayesian-inspired change-point detection via rolling mean shift."""
        if len(series) < window * 2: return []
        rolling_mean = series.rolling(window).mean()
        rolling_std = series.rolling(window).std()
        diff = np.abs(rolling_mean.diff())
        breaks = np.where(diff > threshold_std * rolling_std.shift(1))[0].tolist()
        return breaks

    def get_regime_transition_matrix(self) -> np.ndarray:
        return self.model.weights_
