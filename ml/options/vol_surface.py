from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List, Tuple

logger = logging.getLogger("golden_bot.ml.volatility")

class VolatilitySurface:
    """Reconstructs IV Surface and calculates Skew."""
    def __init__(self):
        # Key: (strike, expiry), Value: IV
        self._data: Dict[Tuple[float, float], float] = {}

    def update_iv(self, strike: float, expiry: float, iv: float) -> None:
        self._data[(strike, expiry)] = iv

    def get_skew(self, expiry: float, atm_strike: float) -> float:
        """Calculates 25-Delta Skew: IV(25d put) - IV(25d call)."""
        # Simplified: Find strikes at approx +/- 10% of ATM for proxy
        put_strike = atm_strike * 0.90
        call_strike = atm_strike * 1.10

        iv_put = self._get_nearest_iv(put_strike, expiry)
        iv_call = self._get_nearest_iv(call_strike, expiry)

        if iv_put and iv_call:
            return iv_put - iv_call
        return 0.0

    def _get_nearest_iv(self, target_strike: float, expiry: float) -> float:
        # Brute force nearest neighbor for Phase 15 structure
        best_diff = float('inf')
        best_iv = None
        for (s, e), iv in self._data.items():
            if e == expiry:
                diff = abs(s - target_strike)
                if diff < best_diff:
                    best_diff = diff
                    best_iv = iv
        return best_iv
