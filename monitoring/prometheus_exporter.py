from __future__ import annotations
import logging
from prometheus_client import start_http_server, Summary, Gauge, Histogram

logger = logging.getLogger("golden_bot.monitoring")

REQUEST_TIME = Summary('bot_request_seconds', 'Time spent processing request')
BOT_BALANCE = Gauge('bot_balance_usdt', 'Current wallet balance')
TRADE_LATENCY = Histogram('bot_trade_latency_ms', 'Trade execution latency')

class MonitoringExporter:
    def __init__(self, port: int = 9090):
        self.port = port

    def start(self) -> None:
        start_http_server(self.port)
        logger.info(f"📊 Prometheus metrics exposed on port {self.port}")

    def record_trade(self, latency_ms: float, balance: float) -> None:
        TRADE_LATENCY.observe(latency_ms)
        BOT_BALANCE.set(balance)
