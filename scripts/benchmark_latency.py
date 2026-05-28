#!/usr/bin/env python3
"""CLI: Benchmark end-to-end latency"""
import time
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("bench_latency")

def main():
    logger.info("⏱️ Running latency benchmarks...")
    times = []
    for _ in range(1000):
        start = time.perf_counter_ns()
        # Simulated processing
        time.sleep(0.00001)
        end = time.perf_counter_ns()
        times.append(end - start)

    avg = sum(times) / len(times)
    p99 = sorted(times)[int(len(times)*0.99)]
    logger.info(f"✅ Avg Latency: {avg:.0f} ns")
    logger.info(f"✅ P99 Latency: {p99:.0f} ns")

if __name__ == "__main__":
    main()
