from __future__ import annotations
import logging
import optuna
import pandas as pd
from typing import Callable

logger = logging.getLogger("golden_bot.optuna")

def run_hp_search(objective_fn: Callable, n_trials: int = 50, timeout: float = 3600.0) -> optuna.study.Study:
    logger.info(f"🔍 Starting Optuna HP search: {n_trials} trials")
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective_fn, n_trials=n_trials, timeout=timeout)
    logger.info(f"✅ Best trial: {study.best_trial.value:.4f} | Params: {study.best_trial.params}")
    return study
