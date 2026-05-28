from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("golden_bot.monte_carlo")

@dataclass
class ScenarioResult:
    final_equity: float
    max_drawdown: float
    sharpe: float
    ruin_probability: float

class MonteCarloSimulator:
    """Trade sequence shuffling & robustness testing."""
    def __init__(self, base_trades: List[dict], shuffle_method: str = "block"):
        self.trades = base_trades
        self.method = shuffle_method

    def generate_scenarios(self, n: int = 1000, slippage_stdev: float = 0.0005) -> List[ScenarioResult]:
        scenarios = []
        for _ in range(n):
            shuffled = self._shuffle(self.trades)
            perturbed = self._perturb(shuffled, slippage_stdev)
            res = self._compute_metrics(perturbed)
            scenarios.append(res)
        return scenarios

    def _shuffle(self, trades: List[dict]) -> List[dict]:
        if self.method == "block":
            block_size = max(3, len(trades) // 20)
            blocks = [trades[i:i+block_size] for i in range(0, len(trades), block_size)]
            np.random.shuffle(blocks)
            return [t for blk in blocks for t in blk]
        return trades.copy()

    def _perturb(self, trades: List[dict], stdev: float) -> List[dict]:
        perturbed = []
        for t in trades:
            shock = np.random.normal(0, stdev)
            new_pnl = t["pnl"] * (1 + shock)
            perturbed.append({**t, "pnl": new_pnl})
        return perturbed

    def _compute_metrics(self, trades: List[dict]) -> ScenarioResult:
        equity = 10000.0
        peak = 10000.0
        max_dd = 0.0
        returns = []
        for t in trades:
            equity += t["pnl"]
            peak = max(peak, equity)
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)
            returns.append(t["pnl"] / peak)
        sharpe = np.mean(returns) / (np.std(returns) + 1e-9) if returns else 0
        return ScenarioResult(equity, max_dd, sharpe, 0.0) # ruin prob computed via threshold
