from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from scipy.stats import entropy

logger = logging.getLogger("golden_bot.ml.drift")

class DriftMonitor:
    """Population Stability Index (PSI) + ADWIN concept drift detection."""
    def __init__(self, psi_threshold: float = 0.2, window: int = 1000):
        self.psi_thresh = psi_threshold
        self.window = window
        self._ref_dists: Optional[pd.DataFrame] = None

    def set_reference(self, ref_data: pd.DataFrame) -> None:
        self._ref_dists = self._compute_bins(ref_data)

    def compute_psi(self, current_data: pd.DataFrame) -> Dict[str, float]:
        if self._ref_dists is None: raise ValueError("Reference not set")
        curr_dists = self._compute_bins(current_data)
        psi_scores = {}
        for col in curr_dists.columns:
            ref_p = self._ref_dists[col].values + 1e-9
            curr_p = curr_dists[col].values + 1e-9
            psi_scores[col] = np.sum((ref_p - curr_p) * np.log(ref_p / curr_p))
        return psi_scores

    def detect_concept_drift(self, errors: np.ndarray) -> bool:
        """Simple ADWIN-like window splitting for concept drift."""
        if len(errors) < self.window: return False
        recent = errors[-self.window//2:]
        older = errors[-self.window:-self.window//2]
        return abs(np.mean(recent) - np.mean(older)) > 2 * np.std(errors)

    def _compute_bins(self, df: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
        result = {}
        for col in df.columns:
            hist, _ = np.histogram(df[col], bins=n_bins)
            result[col] = hist / hist.sum()
        return pd.DataFrame(result)
