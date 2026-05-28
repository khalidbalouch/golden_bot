import pytest
import numpy as np
import pandas as pd
from ml.regime_hmm import RegimeHMM
from ml.cross_exchange_alpha import CrossExchangeAlpha, ArbitrageSignal
from ml.multi_agent_rl import MultiAgentCoordinator, AgentDecision
from ml.online_learner import ElasticWeightConsolidation
from core.alpha_orchestrator import AlphaOrchestrator
from core.research_agent import AutonomousResearchAgent
from utils.graph_builder import DynamicGraphBuilder

def test_hmm_prediction():
    hmm = RegimeHMM(n_regimes=2)
    data = pd.DataFrame(np.random.randn(100, 2), columns=["a", "b"])
    hmm.fit(data)
    idx, label, conf = hmm.predict_regime(np.array([0.1, -0.1]))
    assert 0 <= idx <= 1
    assert 0.0 <= conf <= 1.0

def test_cross_exchange_arb():
    alpha = CrossExchangeAlpha(min_profit_bps=5.0)
    alpha.update_prices("TEST", "A", 100.0)
    alpha.update_prices("TEST", "B", 100.6)
    sig = alpha.detect_basis_arbitrage("TEST", ["A", "B"])
    assert sig is not None
    assert sig.expected_profit_bps >= 5.0

def test_multi_agent_coordination():
    coord = MultiAgentCoordinator()
    decisions = [AgentDecision("risk", "HOLD", 0.95, 4), AgentDecision("signal", "BUY", 0.8, 3)]
    res = coord.collect_decisions(decisions)
    assert res["consensus"].action == "NO_TRADE"

def test_graph_adjacency():
    gb = DynamicGraphBuilder()
    gb.update_node("BTC", 50000, 100)
    gb.update_node("ETH", 3000, 50)
    gb.update_node("BTC", 50100, 110)
    gb.update_node("ETH", 2950, 40)
    adj = gb.compute_adjacency_matrix()
    assert adj.shape == (2, 2)
    assert np.all(adj >= 0)
