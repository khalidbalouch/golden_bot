from __future__ import annotations
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("golden_bot.ml.derivatives")

class DerivativeFeatures:
    """Funding rate alpha, OI momentum, liquidation proximity."""
    def __init__(self, hist_funding_window: int = 24, liq_threshold_pct: float = 0.005):
        self.hist_fw = hist_funding_window
        self.liq_thresh = liq_threshold_pct
        self._funding_history: List[float] = []
        self._oi_history: List[float] = []

    def push_funding(self, rate: float) -> None:
        self._funding_history.append(rate)
        if len(self._funding_history) > self.hist_fw: self._funding_history.pop(0)

    def push_oi(self, oi: float) -> None:
        self._oi_history.append(oi)
        if len(self._oi_history) > 20: self._oi_history.pop(0)

    def compute_all(self, current_price: float, liq_clusters: Optional[List[float]] = None) -> Dict[str, float]:
        if not self._funding_history or len(self._oi_history) < 2: return {}
        curr_f = self._funding_history[-1]
        avg_f = np.mean(self._funding_history[:-1])
        funding_alpha = (curr_f - avg_f) * 10000  # Bps deviation

        oi_curr = self._oi_history[-1]
        oi_prev = self._oi_history[-2]
        oi_mom = (oi_curr - oi_prev) / (oi_prev + 1e-9)

        # Liquidation proximity
        liq_score = 0.0
        if liq_clusters:
            dists = [abs(current_price - c) / current_price for c in liq_clusters]
            min_dist = min(dists)
            liq_score = max(0.0, 1.0 - (min_dist / self.liq_thresh))

        return {
            "funding_alpha_bps": funding_alpha,
            "oi_momentum": oi_mom,
            "liq_proximity": liq_score,
            "current_funding": curr_f
        }
