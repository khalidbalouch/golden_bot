from __future__ import annotations
import torch
import torch.nn as nn

class FP16Wrapper(nn.Module):
    """Wraps model for Automatic Mixed Precision (AMP) inference."""
    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model
        self.scaler = torch.cuda.amp.GradScaler()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        with torch.autocast(device_type='cuda', dtype=torch.float16):
            return self.model(x)
