from __future__ import annotations
import logging
import time
from typing import Dict, Optional, Any
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry

logger = logging.getLogger("golden_bot.monitoring.metrics")

class MetricsExporter:
    """Prometheus metrics exporter for all Golden Bot components."""
    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry
        self.prefix = "golden_bot"
        self._gauges: Dict[str, Gauge] = {}
        self._counters: Dict[str, Counter] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._register_default_metrics()

    def _register_default_metrics(self):
        self._gauges["balance"] = Gauge(f"{self.prefix}_balance", "Current wallet balance")
        self._gauges["peak_balance"] = Gauge(f"{self.prefix}_peak_balance", "Peak wallet balance")
        self._gauges["daily_pnl"] = Gauge(f"{self.prefix}_daily_pnl", "Daily realized PnL")
        self._gauges["drawdown_pct"] = Gauge(f"{self.prefix}_drawdown_pct", "Current drawdown percentage")
        self._gauges["sharpe_ratio"] = Gauge(f"{self.prefix}_sharpe_ratio", "Rolling 30d Sharpe ratio")
        self._gauges["win_rate"] = Gauge(f"{self.prefix}_win_rate", "Rolling win rate %")
        self._gauges["active_trades"] = Gauge(f"{self.prefix}_active_trades", "Number of open positions")
        self._gauges["model_confidence"] = Histogram(f"{self.prefix}_model_confidence", "Model prediction confidence", buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        self._gauges["feature_psi"] = Gauge(f"{self.prefix}_feature_psi", "Feature PSI drift score", ["feature_name"])
        self._gauges["queue_depth"] = Gauge(f"{self.prefix}_queue_depth", "Pending task queue depth")
        self._counters["trade_executed"] = Counter(f"{self.prefix}_trades_total", "Total executed trades", ["status", "symbol"])
        self._counters["errors"] = Counter(f"{self.prefix}_errors_total", "Total system errors", ["component", "type"])

    def update_account(self, balance: float, peak: float, daily_pnl: float, dd_pct: float) -> None:
        self._gauges["balance"].set(balance)
        self._gauges["peak_balance"].set(peak)
        self._gauges["daily_pnl"].set(daily_pnl)
        self._gauges["drawdown_pct"].set(dd_pct)

    def update_performance(self, sharpe: float, win_rate: float, active: int) -> None:
        self._gauges["sharpe_ratio"].set(sharpe)
        self._gauges["win_rate"].set(win_rate)
        self._gauges["active_trades"].set(active)

    def record_trade(self, status: str, symbol: str) -> None:
        self._counters["trade_executed"].labels(status=status, symbol=symbol).inc()

    def record_error(self, component: str, error_type: str) -> None:
        self._counters["errors"].labels(component=component, type=error_type).inc()

    def record_model_confidence(self, confidence: float) -> None:
        self._gauges["model_confidence"].observe(confidence)

    def update_feature_drift(self, feature: str, psi: float) -> None:
        self._gauges["feature_psi"].labels(feature_name=feature).set(psi)
