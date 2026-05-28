from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
from core.scale_logic import ScaleLogic, ScaleAction
from core.exit_engine import ExitEngine, ExitAction
from core.liquidity_aware import LiquidityAwareExecutor

logger = logging.getLogger("golden_bot.trade_manager")

class TradeFlag(Enum):
    ML = auto()
    META = auto()
    EV_PLUS = auto()
    BREAKEVEN = auto()
    TRAILING = auto()
    SCALED = auto()

@dataclass
class Trade:
    trade_id: str
    symbol: str
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    sl_price: float
    tp1_price: float
    tp2_price: Optional[float] = None
    quantity: float = 0.0
    filled_qty: float = 0.0
    open_time: float = field(default_factory=time.time)
    source: Optional[str] = None
    leverage: int = 1
    flags: set = field(default_factory=set)
    trailing_active: bool = False
    breakeven_moved: bool = False
    scale_count: int = 0
    max_scale_count: int = 3

    def unrealized_pnl(self, current_price: float) -> float:
        diff = current_price - self.entry_price if self.direction == "LONG" else self.entry_price - current_price
        return diff * self.filled_qty
    def pnl_pct(self, current_price: float) -> float:
        return (self.unrealized_pnl(current_price) / (self.entry_price * self.filled_qty + 1e-9)) * 100

class TradeManager:
    """State-driven multi-step trade lifecycle orchestrator."""
    def __init__(self, scale_logic: ScaleLogic, exit_engine: ExitEngine, liq_executor: LiquidityAwareExecutor):
        self.scale_logic = scale_logic
        self.exit_engine = exit_engine
        self.liq_executor = liq_executor
        self._active_trades: Dict[str, Trade] = {}
        self._trade_states: Dict[str, dict] = {}

    def create_trade(self, trade_id: str, symbol: str, direction: str, entry: float, 
                   sl: float, tp1: float, tp2: Optional[float], qty: float, 
                   source: str = "ML", leverage: int = 1) -> Trade:
        trade = Trade(trade_id, symbol, direction, entry, sl, tp1, tp2, qty, qty, 
                    source=source, leverage=leverage)
        trade.flags.add(TradeFlag.ML)
        self._active_trades[trade_id] = trade
        self._trade_states[trade_id] = {"last_eval": time.time(), "extreme_price": entry}
        logger.info(f"📈 Trade opened: {trade_id} {symbol} {direction} @ {entry}")
        return trade

    async def on_market_update(self, symbol: str, current_price: float, features: Optional[dict] = None) -> List[dict]:
        """Called on every WS price update. Evaluates scales & exits."""
        actions = []
        for tid, trade in list(self._active_trades.items()):
            if trade.symbol != symbol: continue
            state = self._trade_states[tid]
            state["extreme_price"] = max(state["extreme_price"], current_price) if trade.direction == "LONG" else min(state["extreme_price"], current_price)

            # 1. Check exit conditions
            exits = self.exit_engine.evaluate_exits(trade, current_price, state)
            actions.extend([{"type": "exit", "trade_id": tid, **e} for e in exits])

            # 2. Check scale conditions (if allowed)
            if trade.scale_count < trade.max_scale_count and features:
                scale = self.scale_logic.evaluate_scale_in(trade, current_price, features)
                if scale: actions.append({"type": "scale_in", "trade_id": tid, **scale})

            # 3. Liquidity pacing for any pending actions
            if actions:
                actions = [self.liq_executor.pace(a, current_price) for a in actions]

            state["last_eval"] = time.time()
        return actions

    def apply_fill(self, trade_id: str, fill_qty: float, fill_price: float) -> None:
        trade = self._active_trades.get(trade_id)
        if trade:
            trade.filled_qty += fill_qty
            trade.entry_price = ((trade.entry_price * (trade.filled_qty - fill_qty)) + (fill_price * fill_qty)) / trade.filled_qty if trade.filled_qty > 0 else trade.entry_price

    def close_trade(self, trade_id: str, reason: str) -> None:
        if trade_id in self._active_trades:
            del self._active_trades[trade_id]
            logger.info(f"🔒 Trade closed: {trade_id} | Reason: {reason}")
