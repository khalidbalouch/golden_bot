import pytest
import numpy as np
import pandas as pd
from utils.risk_metrics import RiskMetricsCalculator

def test_sharpe_calculation():
calc = RiskMetricsCalculator()
returns = pd.Series(np.random.randn(252) * 0.01)
sharpe = calc.compute_sharpe(returns)
assert -3 < sharpe < 3 # Reasonable bounds for random walk

def test_var_calculation():
calc = RiskMetricsCalculator()
returns = pd.Series(np.random.randn(1000) * 0.01)
var_95 = calc.compute_var(returns, 0.95)
assert var_95 < 0 # VaR should be negative for loss threshold
