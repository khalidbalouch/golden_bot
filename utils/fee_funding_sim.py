from __future__ import annotations

FEE_TIERS = {
    "maker_0.02": {"maker": 0.0002, "taker": 0.0004},
    "maker_0.01": {"maker": 0.0001, "taker": 0.0004},
    "maker_0.00": {"maker": 0.0000, "taker": 0.0004}
}

class FeeFundingSimulator:
    def __init__(self, tier: str = "maker_0.02"):
        self.fees = FEE_TIERS.get(tier, FEE_TIERS["maker_0.02"])
        self.accum_volume = 0.0
        self.funding_rate = 0.0001

    def compute_taker(self, price: float, qty: float) -> float:
        return price * qty * self.fees["taker"]

    def compute_maker(self, price: float, qty: float) -> float:
        return price * qty * self.fees["maker"]

    def compute_funding(self, position_size: float, price: float, hours_held: float) -> float:
        return position_size * price * self.funding_rate * (hours_held / 8.0)
