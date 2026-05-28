from __future__ import annotations
import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from utils.fee_funding_sim import FeeFundingSimulator
from utils.market_impact import MarketImpactModel
from utils.latency_simulator import LatencySimulator
from core.execution.state_machine import OrderStateMachine, OrderState

logger = logging.getLogger("golden_bot.backtest")

class BacktestResult:
    def __init__(self):
        self.trades: List[dict] = []
        self.equity_curve: List[Tuple[float, float]] = []
        self.metrics: Dict[str, float] = {}

class BacktestEngine:
    """Core backtesting framework with realistic execution simulation."""
    def __init__(self, initial_capital: float = 10000.0, fee_tier: str = "maker_0.02",
                 slippage_model: str = "volume_weighted", include_funding: bool = True):
        self.capital = initial_capital
        self.equity = initial_capital
        self.fee_sim = FeeFundingSimulator(tier=fee_tier)
        self.impact_model = MarketImpactModel()
        self.latency_sim = LatencySimulator()
        self.include_funding = include_funding
        self.result = BacktestResult()
        self._open_positions: Dict[str, dict] = {}
        self._state_machines: Dict[str, OrderStateMachine] = {}

    def run_backtest(self, signals: pd.DataFrame, market_ pd.DataFrame) -> BacktestResult:
        logger.info(f"🧪 Running backtest: {len(signals)} signals, initial capital ${self.capital:,.2f}")
        self.result = BacktestResult()
        for idx, sig in signals.iterrows():
            ts = sig["timestamp"]
            price = market_.loc[ts, "close"]
            self._process_signal(sig, price, ts)
            self._update_equity(ts)
        self._compute_metrics()
        return self.result

    def _process_signal(self, sig: pd.Series, price: float, ts: int) -> None:
        oid = f"bt_{ts}"
        self._state_machines[oid] = OrderStateMachine(oid)
        self._state_machines[oid].transition(OrderState.SUBMITTED)

        # Simulate latency & queue position
        latency = self.latency_sim.sample_latency(ts)
        fill_prob = self.latency_sim.estimate_fill_prob(sig["qty"], price)

        if fill_prob > 0.7:
            exec_price = price
            if sig["side"] == "BUY": exec_price += self.impact_model.compute(price, sig["qty"], 1.0)
            else: exec_price -= self.impact_model.compute(price, sig["qty"], 1.0)

            fee = self.fee_sim.compute_taker(exec_price, sig["qty"])
            self._open_positions[oid] = {
                "symbol": sig["symbol"], "side": sig["side"], "qty": sig["qty"],
                "entry": exec_price, "sl": sig.get("sl_price", 0),
                "tp": sig.get("tp_price", 0), "fee": fee, "ts": ts
            }
            self._state_machines[oid].transition(OrderState.FILLED)
            logger.debug(f"✅ Filled {oid} @ {exec_price:.4f} (latency={latency:.1f}ms, prob={fill_prob:.2f})")

    def _update_equity(self, ts: int) -> None:
        if not self._open_positions:
            self.result.equity_curve.append((ts, self.equity))
            return
        # Simplified mark-to-market for Phase 6
        unrealized = sum(p["qty"] * (p["entry"] - p["entry"]) for p in self._open_positions.values()) # placeholder
        self.equity = self.capital + unrealized
        self.result.equity_curve.append((ts, self.equity))

    def _compute_metrics(self) -> None:
        if len(self.result.equity_curve) < 2: return
        returns = pd.Series([eq for _, eq in self.result.equity_curve]).pct_change().dropna()
        if len(returns) == 0: return
        self.result.metrics["sharpe"] = (returns.mean() / (returns.std() + 1e-9)) * np.sqrt(252 * 24 * 4)
        self.result.metrics["max_dd"] = (pd.Series([eq for _, eq in self.result.equity_curve]).cummax() - 
                                        pd.Series([eq for _, eq in self.result.equity_curve])).max() / self.capital
        self.result.metrics["win_rate"] = 0.5 # placeholder for closed trades
