#!/usr/bin/env python3
"""CLI: Test Gamma Exposure Calculation"""
import sys
import logging
sys.path.insert(0, ".")
from core.macro_orchestrator import MacroOrchestrator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("calc_gex")

def main():
    logger.info("📐 Initializing Options Engine...")
    orch = MacroOrchestrator()

    # Simulate OI Data
    orch.gex.update_oi(60000, 5000)
    orch.gex.update_oi(62000, 2000)
    orch.gex.update_oi(64000, 10000) # Big Wall
    orch.gex.update_oi(66000, 3000)

    res = orch.get_options_bias("BTCUSDT", 64100.0)

    logger.info(f"💹 Max Pain Strike: ${res['max_pain']:,.2f}")
    logger.info(f"🔄 Gamma Flip Level: ${res['gamma_flip']:,.2f}")
    logger.info("✅ Options analysis complete.")

if __name__ == "__main__":
    main()
