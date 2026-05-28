import pytest
import torch
from ml.acceleration.gpu_inference import GPUInferenceRouter

def test_gpu_router():
    router = GPUInferenceRouter()
    model = torch.nn.Linear(10, 1)
    router.load_model("test_model", model, use_fp16=False)

    inputs = router.batch_inputs([{"f1": 0.5, "f2": 0.2}])
    # If GPU is available, this runs on GPU, else CPU
    out = router.predict("test_model", inputs)
    assert out.shape == (1, 1)
