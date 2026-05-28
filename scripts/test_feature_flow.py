#!/usr/bin/env python3
"""CLI: Validates Phase 4 WS-driven feature pipeline & Dashboard integration"""
import asyncio
import logging
import sys
sys.path.insert(0, ".")
from ml.feature_pipeline import FeaturePipeline
from core.ws_manager import BinanceWSManager

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("test_features")

async def main():
    ws = BinanceWSManager()
    await ws.start(streams=["trade", "depth20@500ms", "markPrice@1s", "fundingRate"], handlers={})
    pipe = FeaturePipeline(ws, symbol="BTCUSDT")
    await pipe.run_validation()

    logger.info("🧪 Simulating WS data for feature computation...")
    for i in range(10):
        pipe._on_trade({"p": str(65000 + i), "q": "0.1", "m": i%2==0})
        pipe._on_depth({"b": [[str(64990-i), "10.0"]], "a": [[str(65010+i), "5.0"]]})
        pipe._on_mark_price({"p": str(65000 + i)})
        pipe._on_funding({"r": "0.0001", "i": str(100000 + i*10)})
        await asyncio.sleep(0.1)

    feats = pipe.get_latest()
    logger.info(f"✅ Feature pipeline output: {list(feats.keys())}")
    logger.info(f"   CVD: {feats.get('cvd',0):.2f}, OB Imb: {feats.get('ob_imbalance',0):.3f}")
    await ws.close()

if __name__ == "__main__": asyncio.run(main())
