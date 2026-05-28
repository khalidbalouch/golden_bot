from __future__ import annotations
import logging
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("golden_bot.ml.cross_exchange")

@dataclass
class ArbitrageSignal:
    symbol: str
    long_exchange: str
    short_exchange: str
    expected_profit_bps: float
    confidence: float
    valid_until: float

class CrossExchangeAlpha:
    """Real-time basis tracking, funding divergence & liquidity migration detection."""
    def __init__(self, min_profit_bps: float = 5.0, max_execution_sec: float = 3.0):
        self.min_profit = min_profit_bps
    self.max_time = max_execution_sec
    self._price_cache: Dict[str, Dict[str, float]] = {}
    self._funding_cache: Dict[str, Dict[str, float]] = {}

    def update_prices(self, symbol: str, exchange: str, price: float) -> None:
        if symbol not in self._price_cache: self._price_cache[symbol] = {}
        self._price_cache[symbol][exchange] = price

    def update_funding(self, symbol: str, exchange: str, rate: float) -> None:
        if symbol not in self._funding_cache: self._funding_cache[symbol] = {}
        self._funding_cache[symbol][exchange] = rate

    def detect_basis_arbitrage(self, symbol: str, exchanges: List[str]) -> Optional[ArbitrageSignal]:
        if symbol not in self._price_cache or len(self._price_cache[symbol]) < 2: return None
        prices = self._price_cache[symbol]
        pairs = [(e1, e2) for i, e1 in enumerate(exchanges) for e2 in exchanges[i+1:]]
        for e1, e2 in pairs:
            if e1 in prices and e2 in prices:
                diff_bps = abs(prices[e1] - prices[e2]) / prices[e1] * 10000
                if diff_bps > self.min_profit:
                    long_ex = e1 if prices[e1] < prices[e2] else e2
                    short_ex = e2 if prices[e1] < prices[e2] else e1
                    return ArbitrageSignal(symbol, long_ex, short_ex, diff_bps, 0.85, time.time() + self.max_time)
        return None

    def detect_funding_divergence(self, symbol: str) -> Optional[Dict[str, float]]:
        if symbol not in self._funding_cache or len(self._funding_cache[symbol]) < 2: return None
        rates = list(self._funding_cache[symbol].values())
        std = np.std(rates)
        mean = np.mean(rates)
        if std > mean * 2.0 and mean != 0:
            return {"symbol": symbol, "divergence_pct": std * 100, "mean_funding": mean}
        return None
