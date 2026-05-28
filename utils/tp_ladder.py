from __future__ import annotations
import logging
from typing import List
from core.trade_manager import Trade
from core.exit_engine import ExitAction

logger = logging.getLogger("golden_bot.tp_ladder")

class TPLadder:
    def __init__(self, levels: List[float] = None, default_allocation: List[float] = None):
        self.levels = levels or [1.5, 2.5, 4.0] # ATR multipliers or fixed %
        self.allocation = default_allocation or [0.5, 0.25, 0.25]

    def evaluate_triggers(self, trade: Trade, current_price: float) -> List[ExitAction]:
        actions = []
        if trade.direction == "LONG":
            if current_price >= trade.tp1_price:
                actions.append(ExitAction("tp_ladder", trade.filled_qty * 0.5, trade.tp1_price, 2, "tp1_hit"))
            if trade.tp2_price and current_price >= trade.tp2_price:
                actions.append(ExitAction("tp_ladder", trade.filled_qty * 0.5, trade.tp2_price, 2, "tp2_hit"))
        else:
            if current_price <= trade.tp1_price:
                actions.append(ExitAction("tp_ladder", trade.filled_qty * 0.5, trade.tp1_price, 2, "tp1_hit"))
            if trade.tp2_price and current_price <= trade.tp2_price:
                actions.append(ExitAction("tp_ladder", trade.filled_qty * 0.5, trade.tp2_price, 2, "tp2_hit"))
        return actions
