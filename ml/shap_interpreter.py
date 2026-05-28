from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import shap

logger = logging.getLogger("golden_bot.ml.shap")

class SHAPInterpreter:
    """Live SHAP attribution with sliding window & drift detection."""
    def __init__(self, model, background: pd.DataFrame, window: int = 100):
        self.model = model
        self._background = background.iloc[:100]
        self._window = window
        self._shap_history: List[pd.DataFrame] = []

    def compute_live_attribution(self, X: pd.DataFrame) -> pd.DataFrame:
        explainer = shap.TreeExplainer(self.model, data=self._background)
        shap_values = explainer.shap_values(X)
        attribution = pd.DataFrame(shap_values, columns=X.columns, index=X.index)
        self._shap_history.append(attribution)
        if len(self._shap_history) > self._window: self._shap_history.pop(0)
        return attribution

    def get_top_drivers(self, X: pd.DataFrame, n: int = 5) -> List[Tuple[str, float]]:
        attr = self.compute_live_attribution(X)
        mean_abs = attr.abs().mean().sort_values(ascending=False)
        return mean_abs.head(n).to_dict().items()

    def detect_feature_drift(self, threshold: float = 0.2) -> List[str]:
        if len(self._shap_history) < 2: return []
        recent = self._shap_history[-1].abs().mean()
        baseline = self._shap_history[0].abs().mean()
        drift = (recent - baseline).abs() / (baseline + 1e-9)
        return drift[drift > threshold].index.tolist()
