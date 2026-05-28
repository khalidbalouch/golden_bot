from __future__ import annotations
import torch
import logging
from typing import Optional
from ml.rl.agents.ppo_agent import PPOAgent

logger = logging.getLogger("golden_bot.rl.continual")

class EWCOnlineLearner:
    """Elastic Weight Consolidation for preventing catastrophic forgetting in RL."""
    def __init__(self, agent: PPOAgent, ewc_lambda: float = 400.0):
        self.agent = agent
        self.ewc_lambda = ewc_lambda
        self.fisher_info: dict = {}
        self.optimal_params: dict = {}
        self._store_optimal_params()

    def compute_fisher_information(self, dataloader, device: str = "cpu") -> None:
        """Approximate Fisher Information Matrix diagonal."""
        self.fisher_info = {n: torch.zeros_like(p) for n, p in self.agent.policy.named_parameters()}
        self.agent.policy.eval()
        for states, targets in dataloader:
            self.agent.optimizer.zero_grad()
            state_tensor = states.to(device)
            _, val = self.agent.policy(state_tensor)
            loss = val.mean() # Placeholder gradient flow
            loss.backward()
            for n, p in self.agent.policy.named_parameters():
                if p.grad is not None:
                    self.fisher_info[n] += p.grad.detach() ** 2
        for n in self.fisher_info:
            self.fisher_info[n] /= len(dataloader)
        self._store_optimal_params()
        logger.info("✅ Fisher Information computed for EWC")

    def ewc_penalty(self) -> torch.Tensor:
        penalty = torch.tensor(0.0)
        for n, p in self.agent.policy.named_parameters():
            if n in self.fisher_info:
                penalty += (self.fisher_info[n] * (p - self.optimal_params[n]) ** 2).sum()
        return self.ewc_lambda * penalty

    def _store_optimal_params(self) -> None:
        self.optimal_params = {n: p.data.clone() for n, p in self.agent.policy.named_parameters()}

    def step_with_ewc(self, loss: torch.Tensor) -> None:
        ewc_loss = self.ewc_penalty()
        total_loss = loss + ewc_loss
        self.agent.optimizer.zero_grad()
        total_loss.backward()
        self.agent.optimizer.step()
