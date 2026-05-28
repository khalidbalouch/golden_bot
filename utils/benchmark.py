from __future__ import annotations
import time
import logging
import psutil
import pandas as pd
from typing import Callable, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger("golden_bot.benchmark")

@dataclass
class BenchmarkResult:
    operation: str
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_ops: float
    peak_memory_mb: float

class PerformanceProfiler:
    """Measures latency, throughput & memory footprint under load."""
    def __init__(self):
        self._process = psutil.Process()

    def profile(self, name: str, func: Callable, iterations: int = 1000, *args, **kwargs) -> BenchmarkResult:
        logger.info(f"📊 Profiling: {name} ({iterations} iterations)")
        latencies = []
        self._process.cpu_percent(interval=None)
        mem_start = self._process.memory_info().rss / 1024**2

        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            latencies.append((time.perf_counter() - start) * 1000)

        mem_end = self._process.memory_info().rss / 1024**2
        latencies.sort()

        return BenchmarkResult(
            operation=name,
            avg_latency_ms=sum(latencies)/len(latencies),
            p95_latency_ms=latencies[int(len(latencies)*0.95)],
            p99_latency_ms=latencies[int(len(latencies)*0.99)],
            throughput_ops=iterations / (sum(latencies)/1000),
            peak_memory_mb=mem_end
        )

    def run_benchmark_suite(self) -> List[BenchmarkResult]:
        from core.security import AuditLogger
        from ml.features_microstructure import MicrostructureFeatures
        from utils.benchmark import PerformanceProfiler

        prof = PerformanceProfiler()
        results = []

        # Audit logging throughput
        audit = AuditLogger()
        results.append(prof.profile("audit_log", lambda: audit.log("SYSTEM_ERROR", None, "bench", "127.0.0.1", "success", "bench"), 5000))

        # Feature computation latency
        mf = MicrostructureFeatures()
        for _ in range(10): mf.push_trade(50000.0, 0.1, True)
        mf.push_orderbook([(49990, 5.0)], [(50010, 5.0)])
        results.append(prof.profile("feature_compute", mf.compute_all, 2000))

        return results
