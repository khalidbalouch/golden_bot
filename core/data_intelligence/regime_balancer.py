from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, Tuple
from scipy.spatial.distance import jensenshannon

logger = logging.getLogger("golden_bot.regime_balancer")

@dataclass
class BalanceReport:
    kl_divergence: float
    original_dist: Dict[str, float]
    target_dist: Dict[str, float]
    passed: bool

class RegimeBalancer:
    def __init__(self, target_ratio: Dict[str, float] = None):
        self.target = target_ratio or {"TREND": 0.3, "CHOP": 0.4, "HIGHVOL": 0.3}
        self.total = sum(self.target.values())
        self.target = {k: v/self.total for k,v in self.target.items()}

    def balance_dataset(self, dataset: pd.DataFrame, regime_col: str) -> pd.DataFrame:
        current = dataset[regime_col].value_counts(normalize=True).to_dict()
        balanced = pd.DataFrame()
        for reg, frac in self.target.items():
            reg_data = dataset[dataset[regime_col] == reg]
            n_current = len(reg_data)
            n_target = int(frac * len(dataset))
            if n_target > n_current:
                sampled = reg_data.sample(n=n_target, replace=True, random_state=42)
            else:
                sampled = reg_data.sample(n=n_target, random_state=42)
            balanced = pd.concat([balanced, sampled])
        return balanced.sample(frac=1.0, random_state=42).reset_index(drop=True)

    def validate_balance(self, balanced: pd.DataFrame, original: pd.DataFrame, regime_col: str) -> BalanceReport:
        orig_dist = original[regime_col].value_counts(normalize=True).to_dict()
        bal_dist = balanced[regime_col].value_counts(normalize=True).to_dict()
        kl = jensenshannon(list(orig_dist.values()), list(self.target.values()))**2
        return BalanceReport(kl_divergence=kl, original_dist=orig_dist, target_dist=self.target, passed=kl < 0.1)
