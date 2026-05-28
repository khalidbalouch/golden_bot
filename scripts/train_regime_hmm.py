#!/usr/bin/env python3
"""CLI: Train HMM regime classifier & detect structural breaks"""
import argparse
import logging
import sys
import pandas as pd
import numpy as np
from ml.regime_hmm import RegimeHMM

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("train_hmm")

def main(data_path: str, regimes: int = 3):
    logger.info(f"📥 Loading features from {data_path}")
    df = pd.read_csv(data_path)
    feats = df[["returns", "volatility", "volume_ratio"]].dropna()

    logger.info(f"🧠 Fitting {regimes}-state HMM...")
    hmm = RegimeHMM(n_regimes=regimes)
    hmm.fit(feats)

    breaks = hmm.detect_structural_break(feats["returns"])
    logger.info(f"✅ Structural breaks detected at indices: {breaks}")
    logger.info("💾 HMM regime classifier ready. Save to model registry.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--regimes", type=int, default=3)
    args = p.parse_args()
    main(args.data, args.regimes)
