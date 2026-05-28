from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

logger = logging.getLogger("golden_bot.ml.timeframe.fractal")

class FractalAnalyzer:
    """Detects fractal dimension synchronization across timeframes."""
    def __init__(self, min_fractal_dim: float = 1.0, max_fractal_dim: float = 2.0):
        self.min_dim = min_fractal_dim
        self.max_dim = max_fractal_dim

    def compute_fractal_dimension(self, prices: pd.Series, scale_range: Tuple[int, int] = (2, 10)) -> float:
        """Higuchi Fractal Dimension estimation."""
        if len(prices) < scale_range[1]: return 1.0
        x = prices.values
        k_max = scale_range[1]
        l_k = np.zeros(k_max - scale_range[0])
        for i, k in enumerate(range(scale_range[0], k_max + 1)):
            l = np.sum(np.abs(np.diff(x, n=k))) / k
            l_k[i] = np.log(l + 1e-9)
        x_vals = np.log(np.arange(scale_range[0], k_max + 1))
        slope = np.polyfit(x_vals, l_k, 1)[0]
        return min(self.max_dim, max(self.min_dim, 2.0 - slope))

    def detect_fractal_synchronization(self, symbols_dims: Dict[str, float]) -> float:
        """Measures cross-symbol fractal alignment (market-wide regime signal)."""
        if len(symbols_dims) < 2: return 0.0
        return 1.0 - np.std(list(symbols_dims.values()))

    def align_fractal_trends(self, dims_history: Dict[str, List[float]]) -> Dict[str, float]:
        """Checks if fractal dimension trends align across timeframes for a single symbol."""
        alignment_scores = {}
        for sym, dims in dims_history.items():
            if len(dims) < 2: alignment_scores[sym] = 0.5; continue
            trend = np.polyfit(range(len(dims)), dims, 1)[0]
            volatility = np.std(dims)
            alignment_scores[sym] = np.clip(1.0 - (volatility * 10.0), 0.0, 1.0)
        return alignment_scores
