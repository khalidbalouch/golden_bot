#!/usr/bin/env python3
"""CLI: Evolve trading strategy parameters using Genetic Algorithms"""
import argparse
import logging
import sys
sys.path.insert(0, ".")
from ml.discovery.genetic_optimizer import GeneticStrategyOptimizer

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("evolve")

def dummy_fitness(params) -> float:
    # Placeholder: replace with actual backtest Sharpe ratio
    import random; return random.gauss(1.5, 0.5)

def main(generations: int = 20):
    bounds = {"sl_mult": (0.5, 3.0), "tp_mult": (1.0, 5.0), "rsi_period": (10, 30)}
    optimizer = GeneticStrategyOptimizer(bounds, fitness_func=dummy_fitness, ngen=generations)
    best = optimizer.run_evolution()
    logger.info(f"🧬 Best Evolved Parameters: {best}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--generations", type=int, default=20)
    args = p.parse_args()
    main(args.generations)
