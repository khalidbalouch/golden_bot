#!/usr/bin/env python3
"""CLI: Historical Kelly fraction estimation with safety margin"""
import argparse
import logging
import sys
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("kelly_calibrate")

def main(trades_path: str, fractional: float = 0.25):
    logger.info(f"📊 Calibrating Kelly fraction from {trades_path}")
    df = pd.read_csv(trades_path)
    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] <= 0]

    win_rate = len(wins) / len(df)
    avg_win = wins["pnl"].mean()
    avg_loss = abs(losses["pnl"].mean())

    b = avg_win / (avg_loss + 1e-9)
    q = 1 - win_rate
    f_kelly = max(0, (win_rate - q/b)) * fractional

    logger.info(f"✅ Kelly Calibration Results:")
    logger.info(f"   Win Rate: {win_rate:.2%}")
    logger.info(f"   Avg Win/Loss: {avg_win:.2f} / {avg_loss:.2f}")
    logger.info(f"   Raw Kelly: {(win_rate - q/b):.3f}")
    logger.info(f"   Recommended Fractional ({fractional}x): {f_kelly:.3f}")
    logger.info(f"   Suggested config.fractional_kelly_coeff = {f_kelly:.3f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--trades", required=True)
    p.add_argument("--fractional", type=float, default=0.25)
    args = p.parse_args()
    main(args.trades, args.fractional)
