from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List

class DynamicGraphBuilder:
    """Constructs real-time asset correlation/flow graphs for GNN input."""
    def __init__(self, window: int = 100):
        self.window = window
        self._price_history: Dict[str, List[float]] = {}
        self._volume_history: Dict[str, List[float]] = {}

    def update_node(self, symbol: str, price: float, volume: float) -> None:
        self._price_history.setdefault(symbol, []).append(price)
        self._volume_history.setdefault(symbol, []).append(volume)
        if len(self._price_history[symbol]) > self.window:
            self._price_history[symbol].pop(0)
            self._volume_history[symbol].pop(0)

    def compute_adjacency_matrix(self) -> np.ndarray:
        symbols = list(self._price_history.keys())
        if len(symbols) < 2: return np.eye(1)
        returns = pd.DataFrame(self._price_history).pct_change().dropna()
        corr = returns.corr().values
        np.fill_diagonal(corr, 0)
        corr = np.maximum(corr, 0)  # Only positive correlations for routing
        return corr / (corr.sum(axis=1, keepdims=True) + 1e-9)

    def get_node_features(self) -> np.ndarray:
        symbols = list(self._price_history.keys())
        feats = []
        for sym in symbols:
            p = self._price_history.get(sym, [0])
            v = self._volume_history.get(sym, [0])
            feats.append([p[-1], np.std(p), np.mean(v), len(v)])
        return np.array(feats)
