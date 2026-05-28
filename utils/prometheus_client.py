from __future__ import annotations
import logging
import threading
from prometheus_client import start_http_server, CollectorRegistry, REGISTRY

logger = logging.getLogger("golden_bot.utils.prometheus")

def start_metrics_server(port: int = 9090, registry: CollectorRegistry = None) -> None:
    """Starts Prometheus metrics HTTP server in a background thread."""
    reg = registry or REGISTRY
    def _run():
        try:
            start_http_server(port, registry=reg)
            logger.info(f"📊 Prometheus metrics exposed on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")

    t = threading.Thread(target=_run, daemon=True, name="PrometheusExporter")
    t.start()
