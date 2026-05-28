from __future__ import annotations
import logging
import pandas as pd
import numpy as np
from typing import List, Dict
from ml.discovery.symbolic_regressor import AlphaSymbolicMiner

logger = logging.getLogger("golden_bot.alpha_miner")

class AutomatedAlphaMiner:
    """Orchestrates symbolic regression & genetic search for alpha generation."""
    def __init__(self):
        self.symbolic = AlphaSymbolicMiner()
        self.discovered_alphas: List[Dict[str, str]] = []

    def run_mining_cycle(self, features: pd.DataFrame, targets: pd.Series, 
                         n_formulas: int = 5) -> List[str]:
        formulas = []
        for _ in range(n_formulas):
            try:
                f = self.symbolic.mine_alpha(features, targets)
                formulas.append(f)
                self.discovered_alphas.append({"formula": f, "score": 0.0})
            except Exception as e:
                logger.warning(f"Alpha mining failed: {e}")
        return formulas
