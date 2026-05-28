from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("golden_bot.ml.multi_agent_rl")

@dataclass
class AgentDecision:
    agent_id: str
    action: str
    confidence: float
    priority: int
    meta dict = None

class MultiAgentCoordinator:
    """Coordinates Signal, Risk, and Execution agents with conflict resolution."""
    def __init__(self, priority_order: List[str] = None):
        self.priority = priority_order or ["risk", "execution", "signal"]
        self._agent_memories: Dict[str, List[dict]] = {}

    def collect_decisions(self, decisions: List[AgentDecision]) -> Dict[str, AgentDecision]:
        """Resolve conflicts using priority-weighted voting & veto rules."""
        if not decisions: return {}
        resolved = {}
        for d in decisions:
            if d.agent_id not in self.priority: continue
            resolved[d.agent_id] = d

        # Risk agent has veto power
        if "risk" in resolved and resolved["risk"].confidence > 0.85 and resolved["risk"].action == "HOLD":
            return {"consensus": AgentDecision("consensus", "NO_TRADE", 0.95, 1)}

        # Execution agent optimizes sizing/pacing
        if "execution" in resolved and "signal" in resolved:
            exec_d = resolved["execution"]
            sig_d = resolved["signal"]
            return {"consensus": AgentDecision("consensus", sig_d.action, (sig_d.confidence + exec_d.confidence)/2, 1)}
        return resolved

    def update_agent_feedback(self, agent_id: str, outcome: dict) -> None:
        self._agent_memories.setdefault(agent_id, []).append(outcome)
        if len(self._agent_memories[agent_id]) > 1000:
            self._agent_memories[agent_id].pop(0)
