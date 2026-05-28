from __future__ import annotations
import logging
import optuna
import pandas as pd
from typing import Callable, Dict

logger = logging.getLogger("golden_bot.ai_optimizer")

class HyperparameterOptimizer:
    """Automated strategy parameter tuning via Optuna."""
    def __init__(self, n_trials: int = 100, timeout: float = 3600.0):
        self.n_trials = n_trials
        self.timeout = timeout

    def optimize(self, backtest_func: Callable[[Dict], float], 
                 param_space: Dict[str, tuple]) -> Dict:
        def objective(trial):
            params = {}
            for name, (low, high, is_int) in param_space.items():
                if is_int:
                    params[name] = trial.suggest_int(name, int(low), int(high))
                else:
                    params[name] = trial.suggest_float(name, float(low), float(high))
            return backtest_func(params)

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout)
        logger.info(f"🧬 Best Params: {study.best_params} | Sharpe: {study.best_value:.3f}")
        return study.best_params
