from __future__ import annotations
import torch
import torch.nn as nn
from typing import Tuple

class TemporalLSTM(nn.Module):
    """LSTM for capturing orderflow & regime temporal dependencies."""
    def __init__(self, input_dim: int, hidden_dim: int = 64, n_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_dim, 1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]
        out = self.fc(self.dropout(last_step))
        return torch.sigmoid(out)

class RegimeTransformer(nn.Module):
    """Lightweight transformer with causal masking for point-in-time correctness."""
    def __init__(self, input_dim: int, d_model: int = 32, nhead: int = 4, num_layers: int = 2):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.head = nn.Linear(d_model, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_proj(x)
        seq_len = x.size(1)
        mask = torch.triu(torch.ones(seq_len, seq_len) * float('-inf'), diagonal=1).to(x.device)
        out = self.encoder(x, mask=mask)
        return torch.sigmoid(self.head(out[:, -1, :]))
