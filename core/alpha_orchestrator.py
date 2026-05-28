from __future__ import annotations
import asyncio
import logging
import time
from typing import Dict, List, Optional
from ml.regime_hmm import RegimeHMM
from ml.cross_exchange_alpha import CrossExchangeAlpha
from ml.multi_agent_rl import MultiAgentCoordinator, AgentDecision
from ml.online_learner import ElasticWeightConsolidation
from utils.graph_builder import DynamicGraphBuilder

logger = logging.getLogger("golden_bot.alpha_orchestrator")

class AlphaOrchestrator:
    """Routes elite alpha signals to execution while managing regime & conflict state."""
    def __init__(self, hmm: RegimeHMM, cross_alpha: CrossExchangeAlpha, coordinator: MultiAgentCoordinator):
        self.hmm = hmm
    self.cross_alpha = cross_alpha
    self.coordinator = coordinator
    self.graph_builder = DynamicGraphBuilder()
    self._running = False
    self._latest_alpha: Dict[str, float] = {}

    async def start(self) -> None:
        self._running = True
        logger.info("🧠 Alpha Orchestrator started (HMM + Cross-Ex + Multi-Agent RL)")
        asyncio.create_task(self._continuous_sync())

    async def process_market_event(self, symbol: str, price: float, features: dict) -> Optional[AgentDecision]:
        # 1. Update cross-exchange caches
        self.cross_alpha.update_prices(symbol, "binance", price)
        self.graph_builder.update_node(symbol, price, features.get("volume", 0))

        # 2. Detect alpha opportunities
        arb = self.cross_alpha.detect_basis_arbitrage(symbol, ["binance", "bybit", "okx"])
        if arb and time.time() < arb.valid_until:
            self._latest_alpha[symbol] = arb.expected_profit_bps
            return AgentDecision("cross_ex", "ENTER_ARBITRAGE", arb.confidence, 2, arb.__dict__)

        # 3. Multi-agent resolution
        decisions = [
            AgentDecision("signal", "EVALUATE", features.get("confidence", 0.5), 3),
            AgentDecision("execution", "SCALE_IN", 0.7, 1),
            AgentDecision("risk", "APPROVE", 0.85, 4)
        ]
        resolved = self.coordinator.collect_decisions(decisions)
        return resolved.get("consensus")

    async def _continuous_sync(self) -> None:
        while self._running:
            await asyncio.sleep(1)

    async def stop(self) -> None: self._running = False
