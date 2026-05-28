from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List

logger = logging.getLogger("golden_bot.ml.gamma")

class GammaExposure:
    """Estimates Dealer Gamma Exposure (GEX) to predict volatility."""
    def __init__(self):
        self._oi: Dict[float, float] = {} # Strike -> Open Interest
        self._gamma_per_contract: float = 0.0 # Simplified constant for now

    def update_oi(self, strike: float, oi: float) -> None:
        self._oi[strike] = oi

    def calculate_net_gex(self, spot_price: float) -> Dict[str, float]:
        """
        Net GEX = Sum(Gamma * OI * Spot^2 * 0.01)
        Positive GEX = Dealers buy dips/sell rips (suppresses vol)
        Negative GEX = Dealers sell dips/buy rips (amplifies vol)
        """
        total_gex = 0.0
        max_pain_strike = 0.0
        max_pain_oi = 0

        # Dealer Gamma approximation
        # Call Gamma > 0, Put Gamma > 0. Dealer is Short Gamma for puts/calls sold.
        # Simplified: We assume we track Net Dealer Position.

        # For this implementation, we calculate "Weighted Open Interest"
        # A proxy for Gamma walls.

        weighted_strikes = []
        for strike, oi in self._oi.items():
            dist = abs(spot_price - strike)
            weight = oi / (dist + 1) # Closer strikes have more impact
            weighted_strikes.append((strike, weight))

            if oi > max_pain_oi:
                max_pain_oi = oi
                max_pain_strike = strike

        if not weighted_strikes:
            return {"net_gex": 0.0, "max_pain": spot_price, "gamma_flip": spot_price}

        # Normalize
        total_w = sum(w for _, w in weighted_strikes)
        gex_center = sum(s * w for s, w in weighted_strikes) / total_w

        # Identify Gamma Flip (where dealers switch from long to short gamma)
        # Usually near highest OI strike or ATM.

        return {
            "net_gex": total_gex, # Placeholder calculation
            "max_pain": max_pain_strike,
            "gamma_flip": gex_center # Price level where vol behavior changes
        }
