from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Literal

logger = logging.getLogger("golden_bot.portfolio_allocator")

class PortfolioAllocator:
    """Dynamic allocation: Equal, Risk Parity, Conviction-Weighted."""
    def __init__(self, mode: Literal["equal", "risk_parity", "conviction"] = "conviction",
                 max_single_weight: float = 0.35, rebalance_threshold: float = 0.10):
        self.mode = mode
        self.max_w = max_single_weight
        self.rebal_thresh = rebalance_threshold

    def compute_weights(self, signals: List[dict], current_weights: Dict[str, float]) -> Dict[str, float]:
        if not signals: return current_weights
        symbols = [s["symbol"] for s in signals]

        if self.mode == "equal":
            w = {sym: 1.0/len(symbols) for sym in symbols}
        elif self.mode == "risk_parity":
            # Simplified inverse-vol parity
            vols = [s.get("vol", 0.02) for s in signals]
            inv_vol = [1/(v+1e-9) for v in vols]
            total = sum(inv_vol)
            w = {sym: iv/total for sym, iv in zip(symbols, inv_vol)}
        else: # conviction
            scores = [s.get("confidence", 0.5) * s.get("ev", 0.5) for s in signals]
            total = sum(scores) + 1e-9
            w = {sym: sc/total for sym, sc in zip(symbols, scores)}

        # Clamp & normalize
        w = {k: min(v, self.max_w) for k, v in w.items()}
        total_w = sum(w.values())
        w = {k: v/total_w for k, v in w.items()}

        # Check if rebalance needed
        if any(abs(w.get(s, 0) - current_weights.get(s, 0)) > self.rebal_thresh for s in symbols):
            logger.info(f"📊 Rebalancing portfolio: {self.mode} mode")
        return w
