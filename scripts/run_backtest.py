#!/usr/bin/env python3
"""CLI: Execute backtest with realistic execution & portfolio simulation"""
import argparse
import logging
import sys
import pandas as pd
from utils.backtest_engine import BacktestEngine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("run_bt")

def main(data_path: str, config: str):
    logger.info(f"📥 Loading market data from {data_path}")
    df = pd.read_csv(data_path)

    engine = BacktestEngine(initial_capital=10000.0, fee_tier="maker_0.02")
    result = engine.run_backtest(df, df)

    logger.info(f"✅ Backtest Complete")
    logger.info(f"   Final Equity: ${result.equity:,.2f}")
    logger.info(f"   Sharpe: {result.metrics.get('sharpe', 0):.3f}")
    logger.info(f"   Max DD: {result.metrics.get('max_dd', 0):.2%}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--config", default="standard")
    args = p.parse_args()
    main(args.data, args.config)
