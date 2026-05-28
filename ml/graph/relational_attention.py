from __future__ import annotations
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional

logger = logging.getLogger("golden_bot.ml.graph.relational")

class RelationalAttentionLayer(nn.Module):
    """Attention mechanism over dynamic asset relationships."""
    def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int = 32, heads: int = 2):
        super().__init__()
        self.heads = heads
        self.node_proj = nn.Linear(node_dim, hidden_dim * heads)
        self.edge_proj = nn.Linear(edge_dim, hidden_dim * heads)
        self.attn_out = nn.Linear(hidden_dim * heads, 1)
        self.norm = nn.LayerNorm(hidden_dim * heads)

    def forward(self, node_features: torch.Tensor, edge_features: torch.Tensor) -> torch.Tensor:
        # node_features: [batch, nodes, node_dim]
        # edge_features: [batch, nodes, nodes, edge_dim] (adjacency/relationship matrix)
        B, N, _ = node_features.shape
        nodes_proj = self.node_proj(node_features).view(B, N, self.heads, -1).permute(0, 2, 1, 3)

        # Compute relational attention scores
        scores = torch.einsum("bhnd,bhmd->bhnm", nodes_proj, nodes_proj) # Simplified attention
        attn_weights = F.softmax(scores, dim=-1)

        out = torch.matmul(attn_weights, nodes_proj).permute(0, 2, 1, 3).contiguous().view(B, N, -1)
        return self.norm(out)
