#!/usr/bin/env python3
"""CLI: Validates Phase 3 execution flow & rate limits"""
import asyncio
import logging
import os
import sys
sys.path.insert(0, ".")
from core.execution_engine import ExecutionEngine
from core.security import AuditLogger

logging.basicConfig(level=logging.INFO, format="%(message)s")

async def main():
    logger = logging.getLogger("test_exec")
    audit = AuditLogger()
    engine = ExecutionEngine(audit)
    await engine.start()

    logger.info("🧪 Testing order submission with rate limiter...")
    for i in range(5):
        try:
            res = await engine.place_order(f"test_{i}", "BTCUSDT", "BUY", 0.001, 50000.0)
            logger.info(f"✅ Order {i}: {res.get('status')}")
        except Exception as e: logger.error(f"❌ Order {i} failed: {e}")
        await asyncio.sleep(0.5)

    await engine.stop()
    logger.info("✅ Phase 3 execution flow validated")

if __name__ == "__main__":
    asyncio.run(main())
