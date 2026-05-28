#!/usr/bin/env python3
"""CLI: Test Macro Correlation and Event Processing"""
import sys
import time
import logging
sys.path.insert(0, ".")
from core.macro_orchestrator import MacroOrchestrator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("scan_macro")

def main():
    logger.info("🌍 Initializing Macro Orchestrator...")
    orch = MacroOrchestrator()

    # Simulate incoming ticks
    for i in range(10):
        price = 65000.0 + (i * 100)
        vol = 1000.0 + (i * 50)
        res = orch.process_tick("BTCUSDT", price, vol, i % 2 == 0, int(time.time()))

    logger.info(f"📊 BTCUSDT VPIN: {res['vpin']:.4f}")
    logger.info(f"📉 DXY Correlation: {res['dxy_corr']:.4f}")
    logger.info(f"🛡️ Risk Multiplier: {res['risk_multiplier']:.2f}")
    logger.info("✅ Macro scan complete.")

if __name__ == "__main__":
    main()
