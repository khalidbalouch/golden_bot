#!/usr/bin/env python3
"""CLI: Run performance benchmarks & generate report"""
import sys
sys.path.insert(0, ".")
from utils.benchmark import PerformanceProfiler

def main():
    profiler = PerformanceProfiler()
    results = profiler.run_benchmark_suite()
    print("\n📈 BENCHMARK RESULTS")
    print("-" * 60)
    for r in results:
        print(f"{r.operation:20s} | Avg: {r.avg_latency_ms:.2f}ms | P95: {r.p95_latency_ms:.2f}ms | Mem: {r.peak_memory_mb:.1f}MB")
    print("-" * 60)
    print("✅ Benchmarks complete. Review thresholds before deployment.")

if __name__ == "__main__": main()
