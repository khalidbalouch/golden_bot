from __future__ import annotations
import asyncio
import logging
import time
from typing import Dict, List, Optional
from ml.timeframe.hierarchical_fusion import HierarchicalFusionEngine, BiasSignal
from ml.timeframe.fractal_analyzer import FractalAnalyzer
from ml.timeframe.alignment_scorer import AlignmentScorer
from ml.timeframe.voting_system import TimeframeVotingSystem, VotingResult

logger = logging.getLogger("golden_bot.multi_tf_decision")

class MultiTFDecisionEngine:
    """Unified decision engine integrating all timeframe & graph signals."""
    def __init__(self):
        self.fusion = HierarchicalFusionEngine()
        self.fractal = FractalAnalyzer()
        self.alignment = AlignmentScorer()
        self.voting = TimeframeVotingSystem()
        self._latest_decisions: Dict[str, Dict] = {}

    async def process_signals(self, symbol: str, tf_data: Dict[str, Dict], regime: str) -> Dict:
        """tf_data: {"1h": {"close": [...], "indicators": ...}, "15m": {...}}"""
        # 1. Compute per-TF scores (simplified placeholder for actual indicator logic)
        tf_scores = {}
        for tf, d in tf_data.items():
            # In prod: compute EMA/MACD/RSI score normalized to [-1, 1]
            tf_scores[tf] = d.get("signal_score", 0.0)

        # 2. Hierarchical Fusion
        bias = self.fusion.compute_top_down_bias(symbol, tf_scores)

        # 3. Fractal Synchronization
        dims = {tf: self.fractal.compute_fractal_dimension(d.get("close", [1])) for tf, d in tf_data.items()}
        sync_score = self.fractal.detect_fractal_synchronization(dims)

        # 4. Alignment Scoring
        htf_score = tf_scores.get(max(tf_scores, key=lambda k: self.fusion._tf_priority(k)), 0.0)
        ltf_scores = [v for k, v in tf_scores.items() if k != max(tf_scores, key=lambda k: self.fusion._tf_priority(k))]
        align_res = self.alignment.compute_alignment(htf_score, ltf_scores, regime, regime)

        # 5. Voting System
        vote_res = self.voting.vote(tf_scores, regime)

        result = {
            "symbol": symbol, "bias": bias, "fractal_sync": sync_score,
            "alignment": align_res, "vote": vote_res, "timestamp": time.time()
        }
        self._latest_decisions[symbol] = result
        return result

    def get_latest(self, symbol: str) -> Optional[Dict]:
        return self._latest_decisions.get(symbol)
