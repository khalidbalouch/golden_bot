from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List
from dataclasses import dataclass

logger = logging.getLogger("golden_bot.ml.timeframe.alignment")

@dataclass
class AlignmentScore:
    score: float
    htf_ltf_agreement: bool
    regime_consistency: bool
    recommended_leverage_multiplier: float

class AlignmentScorer:
    """Cross-timeframe confirmation scoring for signal validation."""
    def __init__(self, agreement_threshold: float = 0.7):
        self.threshold = agreement_threshold

    def compute_alignment(self, htf_signal: float, ltf_signals: List[float], htf_regime: str, ltf_regime: str) -> AlignmentScore:
        agreement = all(np.sign(s) == np.sign(htf_signal) or s == 0 for s in ltf_signals) if htf_signal != 0 else True
        consistency = htf_regime == ltf_regime
        raw_score = (0.6 if agreement else 0.0) + (0.2 if consistency else 0.0) + (0.2 * abs(htf_signal))

        lev_mult = 1.0
        if agreement and consistency: lev_mult = 1.5
        elif agreement: lev_mult = 1.2
        elif not agreement and abs(htf_signal) > 0.5: lev_mult = 0.5 # HTF strong, LTF disagree = caution

        return AlignmentScore(
            score=np.clip(raw_score, 0.0, 1.0),
            htf_ltf_agreement=agreement,
            regime_consistency=consistency,
            recommended_leverage_multiplier=lev_mult
        )
