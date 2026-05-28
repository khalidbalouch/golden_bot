from __future__ import annotations
import logging
import numpy as np
from typing import List, Dict

logger = logging.getLogger("golden_bot.ml.toxicity")

class VPINEstimator:
    """Volume-Synchronized Probability of Informed Trading."""
    def __init__(self, bucket_size: int = 50000): # Volume per bucket
        self.bucket_size = bucket_size
        self._buys = 0.0
        self._sells = 0.0
        self._current_bucket_vol = 0.0
        self._vpin_history: List[float] = []
        self._n_buckets = 50 # Rolling window

    def update_trade(self, volume: float, is_buy: bool) -> float:
        """Process a single trade tick."""
        self._current_bucket_vol += volume
        if is_buy:
            self._buys += volume
        else:
            self._sells += volume

        # Bucket full?
        if self._current_bucket_vol >= self.bucket_size:
            vpin = self._calculate_vpin()
            self._vpin_history.append(vpin)
            if len(self._vpin_history) > self._n_buckets:
                self._vpin_history.pop(0)

            # Reset bucket (residual volume carries over)
            residual = self._current_bucket_vol - self.bucket_size
            self._buys = self._buys * (residual / self._current_bucket_vol) if self._current_bucket_vol > 0 else 0
            self._sells = self._sells * (residual / self._current_bucket_vol) if self._current_bucket_vol > 0 else 0
            self._current_bucket_vol = residual # This logic is simplified

            return vpin
        return self.get_latest_vpin()

    def _calculate_vpin(self) -> float:
        if self._buys + self._sells == 0: return 0.0
        return abs(self._buys - self._sells) / (self._buys + self._sells)

    def get_latest_vpin(self) -> float:
        return self._vpin_history[-1] if self._vpin_history else 0.0

    def is_toxic(self, threshold: float = 0.7) -> bool:
        return self.get_latest_vpin() > threshold
