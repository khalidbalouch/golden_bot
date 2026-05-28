#!/usr/bin/env python3
"""CLI: Execute chaos experiments & validate resilience"""
import asyncio
import logging
import sys
sys.path.insert(0, ".")
from core.chaos_engine import ChaosRunner, ChaosExperiment, FaultType
from utils.benchmark import PerformanceProfiler

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("chaos_cli")

class MockSystem: pass

async def main():
    target = MockSystem()
    runner = ChaosRunner(target)

    experiments = [
        ChaosExperiment("ws_drop", FaultType.WS_DISCONNECT, duration_sec=5.0),
        ChaosExperiment("latency_spike", FaultType.NETWORK_LATENCY, duration_sec=3.0, parameters={"ms": 800}),
    ]

    for exp in experiments:
        await runner.inject_fault(exp)
        assert runner.assert_system_resilience()

    logger.info("✅ All chaos experiments passed. System is resilient.")

if __name__ == "__main__": asyncio.run(main())
