import pytest
import numpy as np
import pandas as pd
from ml.timeframe.hierarchical_fusion import HierarchicalFusionEngine
from ml.timeframe.fractal_analyzer import FractalAnalyzer
from ml.timeframe.alignment_scorer import AlignmentScorer
from ml.timeframe.voting_system import TimeframeVotingSystem
from core.multi_tf_decision import MultiTFDecisionEngine

def test_fusion_bias():
    eng = HierarchicalFusionEngine()
    bias = eng.compute_top_down_bias("TEST", {"4h": 0.8, "15m": 0.6, "5m": -0.2})
    assert bias.direction in ["LONG", "SHORT", "NEUTRAL"]
    assert 0.0 <= bias.confidence <= 1.0

def test_fractal_dim():
    fa = FractalAnalyzer()
    series = pd.Series(np.sin(np.linspace(0, 10, 100)))
    dim = fa.compute_fractal_dimension(series)
    assert 1.0 <= dim <= 2.0

def test_voting_system():
    vs = TimeframeVotingSystem()
    res = vs.vote({"4h": 0.7, "1h": 0.5, "15m": 0.8}, regime="TREND")
    assert res.final_decision == "LONG"
    assert res.consensus_strength > 0.0

@pytest.mark.asyncio
async def test_multi_tf_integration():
    engine = MultiTFDecisionEngine()
    tf_data = {
        "4h": {"close": [1,2,3], "signal_score": 0.5},
        "1h": {"close": [1,2,3], "signal_score": 0.4}
    }
    res = await engine.process_signals("BTC", tf_data, "TREND")
    assert "bias" in res
    assert "vote" in res
