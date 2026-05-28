from __future__ import annotations
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from core.trade_manager import Trade
from utils.trailing_stop import TrailingStop
from utils.tp_ladder import TPLadder
from utils.time_decay import TimeDecayExit

logger = logging.getLogger("golden_bot.exit_engine")

@dataclass
class ExitAction:
    exit_type: str  # "hard_sl", "tp_ladder", "trail", "time_decay"
    qty: float
    price: float
    priority: int
    reason: str

class ExitEngine:
    def __init__(self, trailing: TrailingStop, ladder: TPLadder, time_decay: TimeDecayExit):
        self.trailing = trailing
        self.ladder = ladder
        self.time_decay = time_decay

    def evaluate_exits(self, trade: Trade, current_price: float, state: Dict) -> List[ExitAction]:
        actions = []

        # 1. Hard Stop Loss (Highest Priority)
        if (trade.direction == "LONG" and current_price <= trade.sl_price) or                    (trade.direction == "SHORT" and current_price >= trade.sl_price):
            actions.append(ExitAction("hard_sl", trade.filled_qty, current_price, 1, "hard_stop_hit"))
            return actions

        # 2. TP Ladder
        tp_actions = self.ladder.evaluate_triggers(trade, current_price)
        actions.extend(tp_actions)

        # 3. Trailing Stop
        if trade.trailing_active:
            trail_price = self.trailing.compute(trade, current_price, state)
            if trail_price is not None:
                hit = (trade.direction == "LONG" and current_price <= trail_price) or                               (trade.direction == "SHORT" and current_price >= trail_price)
                if hit:
                    actions.append(ExitAction("trail", trade.filled_qty, trail_price, 3, "trailing_stop_hit"))
                    trade.trailing_active = False

        # 4. Time Decay Exit
        td = self.time_decay.evaluate(trade, current_price)
        if td:
            actions.append(ExitAction("time_decay", trade.filled_qty, current_price, 4, td.reason))

        # Sort by priority & resolve conflicts
        actions.sort(key=lambda a: a.priority)
        return actions[:1] if actions else []  # Execute highest priority only
