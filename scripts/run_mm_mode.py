#!/usr/bin/env python3
"""CLI: Run Golden Bot in Market Making Mode"""
import asyncio
import logging
import sys
import json
sys.path.insert(0, ".")
from core.mm_engine import MarketMakingEngine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("mm_cli")

async def main():
    logger.info("🏦 Starting Golden Bot in Market Making Mode...")

    # Load config
    config = {
        "symbol": "BTCUSDT",
        "max_inventory": 0.5,
        "risk_aversion": 0.1,
        "base_spread_bps": 5.0,
        "min_spread_bps": 1.0,
        "maker_rebate": 0.0002, # 2 bps rebate
        "update_freq_sec": 1.0
    }

    # Mock execution API for demo
    class MockAPI: pass

    engine = MarketMakingEngine("BTCUSDT", config, MockAPI())

    # Simulate data feed updates
    await engine.start()

    try:
        while True:
            await asyncio.sleep(10)
            logger.info("💓 MM Heartbeat...")
    except KeyboardInterrupt:
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
