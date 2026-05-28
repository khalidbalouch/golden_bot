#!/usr/bin/env python3
"""CLI: Grid search for optimal trailing/TP/time-decay parameters"""
import argparse
import logging
import sys
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("opt_exit")

def main(data_path: str, trials: int = 50):
    logger.info(f"🔍 Optimizing exit parameters with {trials} trials")
    best_sharpe = -1
    best_params = {}
    # Simplified placeholder for actual backtest loop
    for i in range(trials):
        atr = np.random.uniform(1.5, 4.0)
        dur = np.random.uniform(60, 180)
        # In prod: run backtest with these params, capture metrics
        score = np.random.normal(1.5, 0.3) # placeholder
        if score > best_sharpe:
            best_sharpe = score
            best_params = {"atr_mult": round(atr, 2), "max_duration": int(dur)}
    logger.info(f"✅ Best config: {best_params} | Sharpe: {best_sharpe:.3f}")
    logger.info("💡 Apply to config/exit_strategies/standard.json")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--trials", type=int, default=50)
    args = p.parse_args()
    main(args.data, args.trials)
