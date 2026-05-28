import pytest
import numpy as np
import pandas as pd
from ml.discovery.genetic_optimizer import GeneticStrategyOptimizer
from ml.discovery.symbolic_regressor import AlphaSymbolicMiner
from ml.alpha_miner import AutomatedAlphaMiner

def test_genetic_optimizer():
bounds = {"a": (0, 10), "b": (-5, 5)}
opt = GeneticStrategyOptimizer(bounds, fitness_func=lambda p: -((p[0]-5)**2 + p[1]**2), pop_size=10, ngen=5)
best = opt.run_evolution()
assert "a" in best

def test_symbolic_miner():
miner = AlphaSymbolicMiner(population_size=20, generations=5)
X = pd.DataFrame({"f1": np.random.randn(50), "f2": np.random.randn(50)})
y = X["f1"] + X["f2"]
formula = miner.mine_alpha(X, y)
assert len(formula) > 0
preds = miner.predict(X)
assert len(preds) == 50

def test_alpha_miner_orchestrator():
miner = AutomatedAlphaMiner()
X = pd.DataFrame(np.random.randn(30, 3))
y = pd.Series(np.random.randn(30))
res = miner.run_mining_cycle(X, y, n_formulas=2)
assert len(res) == 2
