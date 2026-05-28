#!/usr/bin/env python3
"""CLI: Real-time basis & funding divergence scanner"""
import asyncio
import logging
import sys
from ml.cross_exchange_alpha import CrossExchangeAlpha

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("scan_alpha")

async def main():
    logger.info("🔍 Scanning cross-exchange alpha opportunities...")
    alpha = CrossExchangeAlpha(min_profit_bps=3.0)
    alpha.update_prices("BTCUSDT", "binance", 65000.0)
    alpha.update_prices("BTCUSDT", "bybit", 65085.0)
    alpha.update_prices("ETHUSDT", "binance", 3500.0)
    alpha.update_prices("ETHUSDT", "okx", 3480.0)

    for sym in ["BTCUSDT", "ETHUSDT"]:
        arb = alpha.detect_basis_arbitrage(sym, ["binance", "bybit", "okx"])
        if arb:
            logger.info(f"💰 ARB: {arb.symbol} | Long: {arb.long_exchange} | Short: {arb.short_exchange} | Profit: {arb.expected_profit_bps:.1f} bps")
        else:
            logger.info(f"⚖️ No arb for {sym}")

if __name__ == "__main__": asyncio.run(main())
