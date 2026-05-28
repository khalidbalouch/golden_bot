#!/usr/bin/env python3
"""CLI: Mine symbolic alpha formulas from features"""
import argparse
import logging
import sys
import pandas as pd
sys.path.insert(0, ".")
from ml.alpha_miner import AutomatedAlphaMiner

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("mine_alpha")

def main(data_path: str, target_col: str = "returns"):
    logger.info(f"🔍 Mining symbolic alpha from {data_path}")
    df = pd.read_csv(data_path)
    features = df.drop(columns=[target_col, "timestamp"], errors="ignore")
    targets = df[target_col]
    miner = AutomatedAlphaMiner()
    formulas = miner.run_mining_cycle(features, targets, n_formulas=3)
    for f in formulas:
        logger.info(f"📜 Alpha: {f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--target", default="returns")
    args = p.parse_args()
    main(args.data, args.target)
