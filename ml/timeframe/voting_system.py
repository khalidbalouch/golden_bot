from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger("golden_bot.ml.timeframe.voting")

@dataclass
class VotingResult:
    final_decision: str
    weighted_score: float
    consensus_strength: float
    dissenting_tfs: List[str]

class TimeframeVotingSystem:
    """Weighted voting system across timeframes with regime-dependent weights."""
    def __init__(self, default_weights: Dict[str, float] = None):
        self.default_weights = default_weights or {"1d": 0.3, "4h": 0.3, "1h": 0.2, "15m": 0.15, "5m": 0.05}
        self.regime_weights: Dict[str, Dict[str, float]] = {
            "TREND": {"1d": 0.4, "4h": 0.3, "1h": 0.2, "15m": 0.05, "5m": 0.05},
            "CHOP":  {"1d": 0.1, "4h": 0.2, "1h": 0.3, "15m": 0.3, "5m": 0.1},
            "HIGHVOL": {"1d": 0.2, "4h": 0.2, "1h": 0.3, "15m": 0.2, "5m": 0.1}
        }

    def vote(self, tf_signals: Dict[str, float], current_regime: str = "CHOP") -> VotingResult:
        weights = self.regime_weights.get(current_regime, self.default_weights)
        total_weight = sum(weights.get(tf, 0) for tf in tf_signals)
        if total_weight == 0: return VotingResult("NEUTRAL", 0.0, 0.0, [])

        weighted_sum = sum(tf_signals.get(tf, 0) * weights.get(tf, 0) for tf in tf_signals)
        final_score = weighted_sum / total_weight

        decision = "LONG" if final_score > 0.2 else "SHORT" if final_score < -0.2 else "NEUTRAL"
        consensus = 1.0 - np.std([s * weights.get(tf, 0) for tf, s in tf_signals.items()])
        dissenting = [tf for tf, s in tf_signals.items() if np.sign(s) != np.sign(final_score) and s != 0]

        return VotingResult(decision, final_score, consensus, dissenting)
