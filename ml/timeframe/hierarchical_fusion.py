from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Literal
from dataclasses import dataclass

logger = logging.getLogger("golden_bot.ml.timeframe.fusion")

@dataclass
class BiasSignal:
    symbol: str
    direction: Literal["LONG", "SHORT", "NEUTRAL"]
    confidence: float
    supporting_timeframes: List[str]
    conflicting_timeframes: List[str]
    htf_agreement_score: float

class HierarchicalFusionEngine:
    """Top-down bias propagation: HTF dictates regime, LTF triggers entries."""
    def __init__(self, timeframes: List[str] = None, htf_weight: float = 0.6):
        self.timeframes = timeframes or ["1d", "4h", "1h", "15m", "5m"]
        self.hft_weight = htf_weight
        self.ltf_weight = 1.0 - htf_weight

    def compute_top_down_bias(self, symbol: str, tf_signals: Dict[str, float]) -> BiasSignal:
        """tf_signals: {"1h": 0.8, "15m": -0.4, ...} range [-1, 1]"""
        sorted_tfs = sorted(tf_signals.keys(), key=lambda x: self._tf_priority(x), reverse=True)
        htf_score = tf_signals.get(sorted_tfs[0], 0.0)
        ltf_score = np.mean([tf_signals.get(t, 0.0) for t in sorted_tfs[1:]]) if len(sorted_tfs) > 1 else 0.0

        fused = self.hft_weight * htf_score + self.ltf_weight * ltf_score

        direction = "LONG" if fused > 0.2 else "SHORT" if fused < -0.2 else "NEUTRAL"
        agreement = 1.0 - np.std(list(tf_signals.values()))

        return BiasSignal(
            symbol=symbol, direction=direction, confidence=abs(fused),
            supporting_timeframes=[k for k, v in tf_signals.items() if np.sign(v) == np.sign(fused)],
            conflicting_timeframes=[k for k, v in tf_signals.items() if np.sign(v) != np.sign(fused)],
            htf_agreement_score=agreement
        )

    def _tf_priority(self, tf: str) -> int:
        mapping = {"1m": 1, "5m": 2, "15m": 3, "1h": 4, "4h": 5, "1d": 6, "1w": 7}
        return mapping.get(tf, 0)
