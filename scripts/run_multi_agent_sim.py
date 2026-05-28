#!/usr/bin/env python3
"""CLI: Validate multi-agent RL coordination & conflict resolution"""
import asyncio
import logging
import sys
from ml.multi_agent_rl import MultiAgentCoordinator, AgentDecision

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("sim_agents")

async def main():
    logger.info("🤖 Running multi-agent coordination simulation...")
    coord = MultiAgentCoordinator()

    decisions = [
        AgentDecision("signal", "ENTER_LONG", 0.75, 3),
        AgentDecision("risk", "APPROVE", 0.90, 4),
        AgentDecision("execution", "LIMIT_ENTRY", 0.80, 1),
    ]
    resolved = coord.collect_decisions(decisions)
    cons = resolved.get("consensus")
    logger.info(f"✅ Consensus reached: {cons.action} | Confidence: {cons.confidence:.2f}")

if __name__ == "__main__": asyncio.run(main())
