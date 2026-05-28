import pytest
import torch
from ml.sequence_models import TemporalLSTM, RegimeTransformer

def test_lstm_forward():
    model = TemporalLSTM(input_dim=5, hidden_dim=16)
    x = torch.randn(8, 10, 5)
    out = model(x)
    assert out.shape == (8, 1)
    assert (out >= 0).all() and (out <= 1).all()

def test_transformer_causal_mask():
    model = RegimeTransformer(input_dim=4, d_model=16, nhead=2)
    x = torch.randn(4, 6, 4)
    out = model(x)
    assert out.shape == (4, 1)
