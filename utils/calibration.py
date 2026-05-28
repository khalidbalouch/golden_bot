from __future__ import annotations
import logging
import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.calibration import CalibratedClassifierCV

logger = logging.getLogger("golden_bot.calibration")

def calibrate_predictions(model, X_val: np.ndarray, y_val: np.ndarray, method: str = "isotonic"):
    cal = CalibratedClassifierCV(model, method=method, cv=3)
    cal.fit(X_val, y_val)
    logger.info(f"📐 Model calibrated using {method} regression")
    return cal
