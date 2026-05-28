from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List

logger = logging.getLogger("golden_bot.portfolio")

class PortfolioOptimizer:
    """Modern Portfolio Theory & Risk Parity allocation."""
    def __init__(self, target_return: float = 0.15, risk_free_rate: float = 0.05):
        self.target_ret = target_return
        self.rf = risk_free_rate

    def calculate_efficient_frontier(self, expected_returns: pd.Series, 
                                     cov_matrix: pd.DataFrame) -> pd.DataFrame:
        # Simplified Mean-Variance Optimization placeholder
        # In production: use scipy.optimize.minimize
        n = len(expected_returns)
        return pd.DataFrame(np.eye(n), columns=expected_returns.index)

    def risk_parity_weights(self, cov_matrix: pd.DataFrame) -> pd.Series:
        """Allocates capital so each asset contributes equal risk."""
        vols = np.sqrt(np.diag(cov_matrix))
        inv_vols = 1.0 / (vols + 1e-9)
        weights = inv_vols / inv_vols.sum()
        return pd.Series(weights, index=cov_matrix.index)

    def dynamic_rebalance(self, current_weights: Dict[str, float], 
                          target_weights: Dict[str, float], threshold: float = 0.05) -> List[str]:
        """Returns list of symbols that need rebalancing."""
        actions = []
        for sym in set(list(current_weights.keys()) + list(target_weights.keys())):
            curr = current_weights.get(sym, 0.0)
            targ = target_weights.get(sym, 0.0)
            if abs(curr - targ) > threshold:
                actions.append(sym)
        return actions
