from __future__ import annotations
import logging
import numpy as np
from typing import Tuple

logger = logging.getLogger("golden_bot.mm.as_model")

class AvellanedaStoikov:
    """Calculates optimal bid/ask prices and reservation price."""
    def __init__(self, risk_aversion: float = 0.1, inventory_penalty: float = 0.5):
        self.gamma = risk_aversion  # Risk aversion coefficient
        self.q_penalty = inventory_penalty # Inventory skew factor

    def calculate_reservation_price(self, mid_price: float, inventory: float, 
                                    volatility: float, time_horizon: float) -> float:
        """
        Reservation Price = s - q * gamma * sigma^2 * (T-t)
        Adjusts the "true" price based on inventory risk.
        """
        if volatility == 0 or time_horizon == 0:
            return mid_price
        adjustment = -inventory * self.gamma * (volatility ** 2) * time_horizon
        return mid_price + adjustment

    def calculate_optimal_spread(self, volatility: float, intensity_lambda: float = 1.0) -> float:
        """
        Optimal Spread = 2/gamma * ln(1 + gamma/lambda)
        Balances probability of execution vs profit per trade.
        """
        # Simplified spread calculation based on vol
        # In full AS model, spread is a function of intensity lambda
        base_spread = volatility * 2.0 
        return max(base_spread, 0.0001) # Minimum spread floor

    def get_quotes(self, mid_price: float, inventory: float, 
                   volatility: float, time_horizon: float) -> Tuple[float, float]:
        r = self.calculate_reservation_price(mid_price, inventory, volatility, time_horizon)
        half_spread = self.calculate_optimal_spread(volatility) / 2.0

        bid = r - half_spread
        ask = r + half_spread

        # Ensure bid < ask
        if bid >= ask:
            mid = (bid + ask) / 2
            gap = max(0.0001, volatility * 0.1)
            bid = mid - gap
            ask = mid + gap

        return bid, ask
