import pytest
from prometheus_client import CollectorRegistry
from monitoring.metrics_exporter import MetricsExporter

def test_metric_registration():
registry = CollectorRegistry()
exporter = MetricsExporter(registry=registry)
exporter.update_account(10000.0, 10500.0, 150.0, 0.05)
exporter.record_trade("filled", "BTCUSDT")

# Verify metrics are populated
samples = list(registry.collect())
assert len(samples) > 0
