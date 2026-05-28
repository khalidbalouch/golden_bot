from __future__ import annotations
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple

logger = logging.getLogger("golden_bot.ml.gnn")

class GraphAttentionLayer(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.heads = heads
        self.out_dim = out_dim
        self.W = nn.Linear(in_dim, out_dim * heads, bias=False)
        self.a_src = nn.Parameter(torch.Tensor(out_dim * heads))
        self.a_tgt = nn.Parameter(torch.Tensor(out_dim * heads))
        self.dropout = nn.Dropout(dropout)
        nn.init.xavier_normal_(self.W.weight)
        nn.init.xavier_normal_(self.a_src)
        nn.init.xavier_normal_(self.a_tgt)

    def forward(self, h: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        B, N, _ = h.shape
        Wh = self.W(h).view(B, N, self.heads, self.out_dim).transpose(1, 2)
        e = (Wh @ self.a_src).squeeze(-1) + (Wh @ self.a_tgt).squeeze(-1).transpose(-1, -2)
        attention = F.softmax(e + (adj == 0).float() * -1e9, dim=-1)
        attention = self.dropout(attention)
        h_prime = torch.matmul(attention, Wh).transpose(1, 2).contiguous().view(B, N, self.out_dim * self.heads)
        return F.elu(h_prime)

class CrossAssetGNNEncoder(nn.Module):
    """GNN for learning cross-asset dependency embeddings."""
    def __init__(self, node_features: int, hidden_dim: int = 32, heads: int = 2, layers: int = 2):
        super().__init__()
        self.layers = nn.ModuleList([GraphAttentionLayer(node_features if i == 0 else hidden_dim * heads, hidden_dim, heads) for i in range(layers)])
        self.heads = heads
    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        for layer in self.layers:
            x = layer(x, adj)
        return x.mean(dim=1)  # Pool to graph-level embedding
