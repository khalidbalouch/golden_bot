#!/usr/bin/env python3
"""CLI: Validate alert routing & webhook dispatch"""
import asyncio
import logging
import sys
sys.path.insert(0, ".")
from monitoring.alert_manager import AlertManager, Alert

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("test_alerts")

async def main():
    logger.info("🧪 Testing alert manager routing & deduplication...")
    manager = AlertManager(dedup_window_sec=2)

    # Simulate metric breach
    metrics = {"drawdown_pct": 0.12, "psi": 0.05, "queue_depth": 50}
    triggered = await manager.evaluate_rules(metrics)

    assert len(triggerged) == 1
    assert triggered[0].rule_name == "high_drawdown"
    logger.info(f"✅ Alert dispatched: {triggered[0].rule_name} [{triggered[0].severity}]")

    # Test deduplication
    triggered2 = await manager.evaluate_rules(metrics)
    assert len(triggered2) == 0
    logger.info("✅ Deduplication working correctly")

if __name__ == "__main__":
    asyncio.run(main())
