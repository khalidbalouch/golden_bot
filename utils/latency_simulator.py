from __future__ import annotations
import numpy as np
from typing import Optional

class LatencySimulator:
    """Realistic order fill modeling with queue position & latency."""
    def __init__(self, base_latency_ms: float = 150.0, stdev: float = 50.0):
        self.base = base_latency_ms
        self.stdev = stdev

    def sample_latency(self, ts: Optional[int] = None) -> float:
        return max(10.0, np.random.normal(self.base, self.stdev))

    def estimate_fill_prob(self, order_qty: float, current_price: float, limit_offset: float = 0.0) -> float:
        if limit_offset == 0: return 1.0 # market order
        prob = 1.0 / (1.0 + np.exp(-5 * (limit_offset / current_price)))
        return min(0.99, max(0.05, prob))
