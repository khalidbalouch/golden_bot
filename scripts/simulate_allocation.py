#!/usr/bin/env python3
"""CLI: Allocation strategy backtesting with transaction costs"""
import argparse
import logging
import sys
import pandas as pd
from core.portfolio_allocator import PortfolioAllocator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("alloc_sim")

def main(signals_path: str, mode: str = "conviction"):
    logger.info(f"📈 Simulating {mode} allocation strategy")
    signals = pd.read_csv(signals_path).to_dict("records")

    allocator = PortfolioAllocator(mode=mode)
    weights = allocator.compute_weights(signals, {})

    logger.info(f"✅ Target Allocation Weights:")
    for sym, w in weights.items():
        logger.info(f"   {sym}: {w:.2%}")

    total = sum(weights.values())
    logger.info(f"   Sum: {total:.2%} (should be 100%)")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--signals", required=True)
    p.add_argument("--mode", choices=["equal", "risk_parity", "conviction"], default="conviction")
    args = p.parse_args()
    main(args.signals, args.mode)
