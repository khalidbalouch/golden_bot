from __future__ import annotations
import logging
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass
from core.trade_manager import Trade

logger = logging.getLogger("golden_bot.scale_logic")

@dataclass
class ScaleAction:
    qty: float
    price_limit: Optional[float]
    reason: str

class ConvictionTracker:
    def __init__(self, ema_span: int = 20):
        self.span = ema_span
        self._history: list[float] = []

    def update(self, confidence: float) -> float:
        self._history.append(confidence)
        if len(self._history) > self.span: self._history.pop(0)
        return float(np.mean(self._history[-self.span:]))

    def delta(self) -> float:
        if len(self._history) < 2: return 0.0
        return self._history[-1] - self._history[0]

class ScaleLogic:
    def __init__(self, min_conviction_delta: float = 0.10, max_total_risk_pct: float = 0.03):
        self.min_delta = min_conviction_delta
        self.max_risk = max_total_risk_pct
        self.trackers: Dict[str, ConvictionTracker] = {}

    def evaluate_scale_in(self, trade: Trade, current_price: float, features: Dict) -> Optional[ScaleAction]:
        tid = trade.trade_id
        if tid not in self.trackers: self.trackers[tid] = ConvictionTracker()

        conf = features.get("probability", features.get("confidence", 0.5))
        self.trackers[tid].update(conf)

        delta = self.trackers[tid].delta()
        if delta < self.min_delta: return None

        # Check if price pulled back favorably
        pullback_ok = False
        if trade.direction == "LONG" and current_price <= trade.entry_price * 1.005:
            pullback_ok = True
        elif trade.direction == "SHORT" and current_price >= trade.entry_price * 0.995:
            pullback_ok = True

        if not pullback_ok: return None

        # Compute additional size (fixed fraction of initial for simplicity)
        add_qty = trade.quantity * 0.3
        logger.info(f"📊 Scale-in triggered for {tid}: +{add_qty} (conviction Δ={delta:.3f})")
        return ScaleAction(add_qty, current_price, f"conviction_delta_{delta:.2f}")

    def evaluate_scale_out(self, trade: Trade, current_price: float, features: Dict) -> Optional[ScaleAction]:
        # Placeholder for dynamic scale-out logic (can be extended later)
        return None
