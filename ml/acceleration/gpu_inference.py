from __future__ import annotations
import logging
import torch
import torch.nn as nn
from typing import Dict, List
from ml.acceleration.mixed_precision import FP16Wrapper

logger = logging.getLogger("golden_bot.acceleration.gpu")

class GPUInferenceRouter:
    """Routes inference requests to optimal GPU based on load & model size."""
    def __init__(self, device_map: Dict[str, torch.device] = None):
        self.device_map = device_map or {"default": torch.device("cuda" if torch.cuda.is_available() else "cpu")}
        self._cache: Dict[str, nn.Module] = {}

    def load_model(self, model_id: str, model: nn.Module, use_fp16: bool = True) -> None:
        device = self.device_map.get("default")
        if use_fp16 and device.type == "cuda":
            model = FP16Wrapper(model)
        self._cache[model_id] = model.to(device).eval()
        logger.info(f"📦 Model {model_id} loaded on {device}")

    def predict(self, model_id: str, inputs: torch.Tensor) -> torch.Tensor:
        if model_id not in self._cache: raise RuntimeError(f"Model {model_id} not loaded")
        device = self._cache[model_id].device
        inputs = inputs.to(device)
        with torch.no_grad():
            return self._cache[model_id](inputs)

    def batch_inputs(self, inputs: List[Dict]) -> torch.Tensor:
        """Converts list of dicts to padded tensor for batch inference."""
        # Simplified batching
        vals = torch.tensor([list(v.values()) for v in inputs], dtype=torch.float32)
        return vals
