from __future__ import annotations
import logging
import numpy as np
import torch
from typing import Dict, Optional
from torch import nn, optim

logger = logging.getLogger("golden_bot.ml.online_learner")

class ElasticWeightConsolidation(nn.Module):
    """Continual learning via EWC to prevent catastrophic forgetting."""
    def __init__(self, model: nn.Module, lambda_ewc: float = 5000.0):
        super().__init__()
        self.model = model
        self.lambda_ewc = lambda_ewc
        self.fisher: Dict[str, torch.Tensor] = {}
        self.optimal_params: Dict[str, torch.Tensor] = {}
        self._store_optimal_params()

    def compute_fisher(self, data_loader, device: torch.device = "cpu") -> None:
        self.fisher = {n: torch.zeros(p.size()).to(device) for n, p in self.model.named_parameters() if p.requires_grad}
        self.model.eval()
        for x, y in data_loader:
            self.model.zero_grad()
            out = self.model(x.to(device))
            loss = nn.CrossEntropyLoss()(out, y.to(device))
            loss.backward()
            for n, p in self.model.named_parameters():
                if p.grad is not None:
                    self.fisher[n] += p.grad.data ** 2
        for n in self.fisher:
            self.fisher[n] /= len(data_loader)
        self._store_optimal_params()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

    def ewc_loss(self, device: torch.device) -> torch.Tensor:
        loss = torch.tensor(0.0, device=device)
        for n, p in self.model.named_parameters():
            if n in self.fisher and n in self.optimal_params:
                loss += (self.fisher[n] * (p - self.optimal_params[n]) ** 2).sum()
        return self.lambda_ewc * loss

    def _store_optimal_params(self) -> None:
        self.optimal_params = {n: p.data.clone().detach() for n, p in self.model.named_parameters()}
