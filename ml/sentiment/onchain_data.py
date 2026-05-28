from __future__ import annotations
import logging
from typing import Dict

logger = logging.getLogger("golden_bot.sentiment.onchain")

class OnChainMetrics:
    """Placeholder for Glassnode/CryptoQuant integration."""
    def get_exchange_netflow(self, asset: str) -> float:
        # Positive = inflow to exchanges (bearish), Negative = outflow (bullish)
        return 0.0 # Fetch via API in production

    def get_active_addresses(self, asset: str, days: int = 7) -> int:
        return 0 # Fetch via API
