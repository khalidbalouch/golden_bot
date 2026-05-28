#!/usr/bin/env python3
"""CLI: Post-backtest analytics & robustness visualization"""
import argparse
import logging
import sys
import pandas as pd
from utils.monte_carlo import MonteCarloSimulator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("analyze")

def main(trades_path: str, n_scenarios: int = 1000):
    logger.info(f"📊 Analyzing robustness with {n_scenarios} Monte Carlo scenarios")
    trades = pd.read_csv(trades_path).to_dict("records")
    sim = MonteCarloSimulator(trades, shuffle_method="block")
    scenarios = sim.generate_scenarios(n_scenarios)

    equities = [s.final_equity for s in scenarios]
    dds = [s.max_drawdown for s in scenarios]
    logger.info(f"✅ Robustness Report:")
    logger.info(f"   Median Final Equity: ${pd.Series(equities).median():,.2f}")
    logger.info(f"   P10 DD: {pd.Series(dds).quantile(0.1):.2%}")
    logger.info(f"   P90 DD: {pd.Series(dds).quantile(0.9):.2%}")
    logger.info(f"   Risk of Ruin (<50% equity): {(pd.Series(equities) < 5000).mean():.2%}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--trades", required=True)
    p.add_argument("--scenarios", type=int, default=1000)
    args = p.parse_args()
    main(args.trades, args.scenarios)
