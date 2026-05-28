from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List

logger = logging.getLogger("golden_bot.corr_tracker")

class CorrelationTracker:
    """Rolling covariance estimation & sector exposure monitoring."""
    def __init__(self, window: int = 500, decay: float = 0.94):
        self.window = window
        self.decay = decay
        self._returns_history: pd.DataFrame = pd.DataFrame()

    def update(self, returns: Dict[str, float]) -> None:
        new_row = pd.DataFrame([returns])
        self._returns_history = pd.concat([self._returns_history, new_row], ignore_index=True)
        if len(self._returns_history) > self.window:
            self._returns_history = self._returns_history.iloc[-self.window:]

    def get_covariance_matrix(self) -> pd.DataFrame:
        if len(self._returns_history) < 10: return pd.DataFrame()
        # Exponentially weighted covariance
        return self._returns_history.ewm(span=20).cov().iloc[-len(self._returns_history.columns):]

    def compute_portfolio_vol(self, weights: np.ndarray) -> float:
        if self._returns_history.empty: return 0.0
        cov = self._returns_history.cov().values
        return float(np.sqrt(weights @ cov @ weights))

    def detect_concentration(self, weights: Dict[str, float], threshold: float = 0.4) -> List[str]:
        return [sym for sym, w in weights.items() if w > threshold]
