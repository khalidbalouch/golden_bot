from __future__ import annotations
import torch
import torch.nn as nn
import random
from typing import Dict, List

class NASController:
    """Neural Architecture Search for LSTM/Transformer configs."""
    def __init__(self, search_space: Dict[str, List[int]]):
        self.space = search_space # e.g. {"layers": [1,2,3], "hidden": [32,64,128]}

    def sample_architecture(self) -> Dict[str, int]:
        return {k: random.choice(v) for k, v in self.space.items()}

    def train_architecture(self, arch: Dict[str, int], train_loader, val_loader) -> float:
        """Quickly trains a model with given arch and returns val loss."""
        model = self._build_model(arch)
        # Placeholder training loop
        loss = 1.0
        return loss

    def _build_model(self, arch: Dict[str, int]) -> nn.Module:
        class SearchNet(nn.Module):
            def __init__(self, layers, hidden):
                super().__init__()
                self.lstm = nn.LSTM(10, hidden, layers, batch_first=True)
                self.fc = nn.Linear(hidden, 1)
            def forward(self, x): return self.fc(x[:, -1, :])
        return SearchNet(arch["layers"], arch["hidden"])
