from __future__ import annotations
import asyncio
import logging
import time
from typing import Dict, Optional
import pandas as pd

logger = logging.getLogger("golden_bot.prediction")

class PredictionService:
    """Async prediction API with caching, fallback, and drift awareness."""
    def __init__(self, model, conformal=None, cache_ttl: float = 1.0):
        self.model = model
        self.conformal = conformal
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple] = {}
        self._drift_active = False

    async def predict(self, features: pd.Series) -> Dict[str, float]:
        key = features.to_dict().__str__()
        if key in self._cache and time.time() - self._cache[key][1] < self.cache_ttl:
            return self._cache[key][0]
        try:
            proba = self.model.predict_proba(features.to_frame().T)[:, 1][0]
            if self.conformal:
                lower, mid, upper = self.conformal.predict_with_intervals(np.array([proba]))
                result = {"probability": float(mid), "lower": float(lower[0]), "upper": float(upper[0])}
            else:
                result = {"probability": float(proba)}
            self._cache[key] = (result, time.time())
            return result
        except Exception as e:
            logger.error(f"⚠️ Prediction fallback triggered: {e}")
            return {"probability": 0.5, "lower": 0.3, "upper": 0.7, "fallback": True}

    def mark_drift_active(self, active: bool) -> None:
        self._drift_active = active
        self._cache.clear()
        logger.info(f"🔄 Drift mode: {'ACTIVE' if active else 'INACTIVE'}")
