from __future__ import annotations
import logging
import time
from typing import Optional
from dataclasses import dataclass
from core.trade_manager import Trade

logger = logging.getLogger("golden_bot.time_decay")

@dataclass
class TimeDecayAction:
    reason: str
    urgency: float

class TimeDecayExit:
    def __init__(self, max_duration_min: int = 120, edge_half_life_min: int = 60):
        self.max_dur = max_duration_min * 60
        self.half_life = edge_half_life_min * 60

    def evaluate(self, trade: Trade, current_price: float) -> Optional[TimeDecayAction]:
        elapsed = time.time() - trade.open_time
        if elapsed > self.max_dur:
            return TimeDecayAction("max_duration_exceeded", 1.0)

        # Edge decay: exp(-t / half_life)
        edge_factor = np.exp(-elapsed / self.half_life)
        if edge_factor < 0.3 and trade.pnl_pct(current_price) < 0.2:
            return TimeDecayAction("edge_decayed_below_threshold", edge_factor)
        return None
