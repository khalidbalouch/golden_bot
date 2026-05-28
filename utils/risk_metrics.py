from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict

logger = logging.getLogger("golden_bot.risk_metrics")

class RiskMetricsCalculator:
    """Sharpe, Sortino, Calmar, VaR, Expected Shortfall, Risk-of-Ruin."""
    def __init__(self, risk_free_rate: float = 0.0):
        self.rf = risk_free_rate

    def compute_sharpe(self, returns: pd.Series) -> float:
        excess = returns - self.rf/252
        return float((excess.mean() / (excess.std() + 1e-9)) * np.sqrt(252))

    def compute_sortino(self, returns: pd.Series) -> float:
        excess = returns - self.rf/252
        downside = excess[excess < 0].std()
        return float((excess.mean() / (downside + 1e-9)) * np.sqrt(252))

    def compute_calmar(self, returns: pd.Series, max_dd: float) -> float:
        if max_dd == 0: return 0.0
        return float(returns.mean() * 252 / max_dd)

    def compute_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        return float(np.percentile(returns, (1 - confidence) * 100))

    def compute_expected_shortfall(self, returns: pd.Series, confidence: float = 0.95) -> float:
        threshold = np.percentile(returns, (1 - confidence) * 100)
        return float(returns[returns <= threshold].mean())

    def compute_risk_of_ruin(self, win_rate: float, avg_win: float, avg_loss: float, risk_per_trade: float, capital: float, ruin_level: float = 0.5) -> float:
        # Markov approximation
        if win_rate <= 0.5: return 1.0
        edge = win_rate * avg_win - (1 - win_rate) * abs(avg_loss)
        if edge <= 0: return 1.0
        prob_ruin = (capital / ruin_level) ** (-edge / (risk_per_trade * capital))
        return max(0.0, min(1.0, prob_ruin))
