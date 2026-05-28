from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from typing import Dict, List
from utils.backtest_engine import BacktestEngine, BacktestResult

logger = logging.getLogger("golden_bot.portfolio_bt")

class PortfolioBacktester:
    """Multi-symbol backtesting with correlation-aware margin & sector limits."""
    def __init__(self, symbols: List[str], correlation_matrix: pd.DataFrame, max_sector_exposure: float = 0.4):
        self.symbols = symbols
        self.corr = correlation_matrix
        self.max_sector = max_sector_exposure

    def run(self, signals_by_symbol: Dict[str, pd.DataFrame], market_ Dict[str, pd.DataFrame]) -> BacktestResult:
        logger.info(f"📈 Running portfolio backtest on {len(symbols)} symbols")
        engine = BacktestEngine(initial_capital=10000.0)
        combined_signals = pd.concat(signals_by_symbol.values(), ignore_index=True).sort_values("timestamp")

        # Simplified portfolio execution for Phase 6
        return engine.run_backtest(combined_signals, combined_signals) # placeholder structure

    def compute_correlation_adjusted_margin(self, positions: Dict[str, float]) -> float:
        if not positions: return 0.0
        weights = np.array([positions.get(s, 0) for s in self.symbols])
        cov = self.corr.to_numpy()
        port_vol = np.sqrt(weights @ cov @ weights)
        return port_vol * 0.1 # 10% margin multiplier
