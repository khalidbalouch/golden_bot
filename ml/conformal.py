from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Literal

logger = logging.getLogger("golden_bot.ml.conformal")

class ConformalPredictor:
    """Split conformal prediction for uncertainty quantification with guaranteed coverage."""
    def __init__(self, alpha: float = 0.1):
        self.alpha = alpha
        self._quantile = None

    def calibrate(self, model_preds: np.ndarray, y_true: np.ndarray) -> None:
        scores = np.abs(y_true - model_preds)
        self._quantile = np.quantile(scores, 1 - self.alpha, method="higher")
        logger.info(f"🎯 Conformal calibrated: quantile={self._quantile:.4f}, coverage={(1-self.alpha)*100:.0f}%")

    def predict_with_intervals(self, model_preds: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if self._quantile is None: raise RuntimeError("Must calibrate before predicting")
        lower = model_preds - self._quantile
        upper = model_preds + self._quantile
        return lower, model_preds, upper

    def coverage_check(self, y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
        return float(np.mean((y_true >= lower) & (y_true <= upper)))
