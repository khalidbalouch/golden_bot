from __future__ import annotations
import logging
from typing import Dict, Optional

logger = logging.getLogger("golden_bot.mm.inventory")

class InventoryManager:
    """Manages position limits and skewing for Market Making."""
    def __init__(self, max_inventory: float = 1.0, target_inventory: float = 0.0):
        self.max_inv = max_inventory
    self.target_inv = target_inventory
    self._current_inv: Dict[str, float] = {}

    def update_inventory(self, symbol: str, amount: float) -> None:
        self._current_inv[symbol] = self._current_inv.get(symbol, 0.0) + amount

    def get_inventory(self, symbol: str) -> float:
        return self._current_inv.get(symbol, 0.0)

    def calculate_skew(self, symbol: str) -> float:
        """Returns a skew factor (-1 to 1) based on current inventory."""
        inv = self.get_inventory(symbol)
        if self.max_inv == 0: return 0.0
        ratio = inv / self.max_inv
        # If long inventory, skew bid down (buy less) and ask down (sell easier)
        # If short inventory, skew bid up (buy easier) and ask up (sell less)
        return -ratio 

    def check_limit(self, symbol: str, proposed_amount: float) -> bool:
        """Checks if adding amount breaches max inventory."""
        current = self.get_inventory(symbol)
        if abs(current + proposed_amount) > self.max_inv:
            logger.warning(f"Inventory limit reached for {symbol} ({current} + {proposed_amount})")
            return False
        return True

    def is_overexposed(self, symbol: str, threshold: float = 0.8) -> bool:
        """Returns true if inventory is > 80% of max."""
        inv = self.get_inventory(symbol)
        return abs(inv / self.max_inv) > threshold
