from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional

logger = logging.getLogger("golden_bot.synthetic_gen")

class SyntheticMarketGenerator:
    def __init__(self, base_data: Optional[pd.DataFrame] = None, regime_labels: Optional[pd.Series] = None):
        self.stats = {}
        if base_data is not None:
            for reg in regime_labels.unique():
                subset = base_data[regime_labels == reg]
                self.stats[reg] = {
                    "mean": subset.select_dtypes(include="number").mean(),
                    "std": subset.select_dtypes(include="number").std(),
                    "corr": subset.select_dtypes(include="number").corr()
                }

    def train_generative_model(self) -> None: logger.info("✅ Synthetic model parameters computed from historical data")

    def generate_synthetic_dataset(self, target_size: int, regime_distribution: Dict[str, float]) -> pd.DataFrame:
        rows = []
        for reg, weight in regime_distribution.items():
            n = int(target_size * weight)
            if reg not in self.stats:
                logger.warning(f"No stats for regime {reg}, using uniform defaults")
                df = pd.DataFrame(np.random.randn(n, 6), columns=["open","high","low","close","volume","trades"])
            else:
                mean = self.stats[reg]["mean"].fillna(0)
                std = self.stats[reg]["std"].fillna(1)
                df = pd.DataFrame(np.random.randn(n, len(mean)), columns=mean.index)
                df = df * std + mean
            df["regime"] = reg
            rows.append(df)
        synth = pd.concat(rows, ignore_index=True)
        synth["timestamp"] = pd.date_range("2023-01-01", periods=len(synth), freq="15min")
        logger.info(f"📊 Generated {len(synth)} synthetic rows across {len(regime_distribution)} regimes")
        return synth
