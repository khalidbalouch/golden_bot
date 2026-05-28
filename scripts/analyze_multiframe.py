#!/usr/bin/env python3
"""CLI: Analyze multi-timeframe alignment & fractal synchronization"""
import argparse
import logging
import sys
import pandas as pd
import numpy as np
sys.path.insert(0, ".")
from core.multi_tf_decision import MultiTFDecisionEngine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("analyze_tf")

async def main(symbol: str):
    logger.info(f"📊 Analyzing Multi-TF Alignment for {symbol}...")
    engine = MultiTFDecisionEngine()

    # Simulated TF data
    tf_data = {
        "4h": {"close": np.random.randn(100).cumsum() + 50000, "signal_score": 0.6},
        "1h": {"close": np.random.randn(100).cumsum() + 50000, "signal_score": 0.4},
        "15m": {"close": np.random.randn(100).cumsum() + 50000, "signal_score": 0.2}
    }

    res = await engine.process_signals(symbol, tf_data, regime="TREND")
    logger.info(f"✅ Bias: {res['bias'].direction} (Conf: {res['bias'].confidence:.2f})")
    logger.info(f"✅ Vote: {res['vote'].final_decision} (Consensus: {res['vote'].consensus_strength:.2f})")
    logger.info(f"✅ Fractal Sync: {res['fractal_sync']:.3f}")
    logger.info(f"✅ Alignment Leverage Mult: {res['alignment'].recommended_leverage_multiplier:.2f}x")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="BTCUSDT")
    args = p.parse_args()
    import asyncio
    asyncio.run(main(args.symbol))
