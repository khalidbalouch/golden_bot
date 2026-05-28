#!/usr/bin/env python3
"""CLI: Out-of-sample validation & drift baseline computation"""
import argparse
import logging
import sys
sys.path.insert(0, ".")
from ml.drift_monitor import DriftMonitor
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("validate_model")

def main(train_path: str, val_path: str, target: str):
    train = pd.read_csv(train_path)
    val = pd.read_csv(val_path)

    dm = DriftMonitor()
    dm.set_reference(train.drop(columns=[target]))
    psi = dm.compute_psi(val.drop(columns=[target]))
    high_drift = {k: v for k, v in psi.items() if v > 0.2}

    if high_drift:
        logger.warning(f"⚠️ High drift detected: {high_drift}")
    else:
        logger.info("✅ Feature distributions stable (PSI < 0.2)")

    logger.info("📊 Validation complete. Baseline drift metrics stored.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--train", required=True)
    p.add_argument("--val", required=True)
    p.add_argument("--target", default="label")
    args = p.parse_args()
    main(args.train, args.val, args.target)
