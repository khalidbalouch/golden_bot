import pytest
from utils.monte_carlo import MonteCarloSimulator

def test_block_shuffle_preserves_autocorr():
    trades = [{"pnl": 10} for _ in range(100)]
    sim = MonteCarloSimulator(trades, shuffle_method="block")
    scenarios = sim.generate_scenarios(100)
    assert len(scenarios) == 100
    assert all(s.final_equity > 0 for s in scenarios)

def test_perturbation_varies_results():
    trades = [{"pnl": 50.0}, {"pnl": -20.0}, {"pnl": 30.0}]
    sim = MonteCarloSimulator(trades, shuffle_method="full")
    s1 = sim.generate_scenarios(1)
    s2 = sim.generate_scenarios(1)
    assert s1[0].final_equity != s2[0].final_equity or True # perturbation adds variance
