from __future__ import annotations
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

logger = logging.getLogger("golden_bot.ml.macro")

class MacroCorrelator:
    """Tracks DXY, SPX, Bond Yields correlations with crypto assets."""
    def __init__(self, window: int = 20):
        self.window = window
        self._hist: Dict[str, List[float]] = {}

    def update(self, symbol: str, price: float) -> None:
        self._hist.setdefault(symbol, []).append(price)
        if len(self._hist[symbol]) > self.window + 1:
            self._hist[symbol].pop(0)

    def compute_correlation(self, crypto_sym: str, macro_sym: str) -> float:
        if (crypto_sym not in self._hist or macro_sym not in self._hist or
            len(self._hist[crypto_sym]) < self.window):
            return 0.0

        c_prices = pd.Series(self._hist[crypto_sym]).pct_change().dropna()
        m_prices = pd.Series(self._hist[macro_sym]).pct_change().dropna()

        # Align lengths
        min_len = min(len(c_prices), len(m_prices))
        return float(c_prices.iloc[-min_len:].corr(m_prices.iloc[-min_len:]))

    def get_dxy_impact(self, crypto_sym: str, dxy: float) -> float:
        """DXY typically inversely correlated with BTC."""
        corr = self.compute_correlation(crypto_sym, "DXY")
        # If strong negative correlation (-0.8) and DXY is rising, negative impact
        return corr * dxy 
