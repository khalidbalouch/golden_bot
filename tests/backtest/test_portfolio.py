import pytest
import pandas as pd
import numpy as np
from core.portfolio_backtester import PortfolioBacktester

def test_corr_margin_calc():
corr = pd.DataFrame(np.eye(3), index=["A","B","C"], columns=["A","B","C"])
bt = PortfolioBacktester(["A","B","C"], corr, max_sector_exposure=0.4)
pos = {"A": 1000, "B": -500, "C": 0}
margin = bt.compute_correlation_adjusted_margin(pos)
assert margin >= 0
