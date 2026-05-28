from __future__ import annotations
import logging
import random
import numpy as np
from typing import Dict, Tuple, Callable

logger = logging.getLogger("golden_bot.discovery.genetic")

class GeneticOptimizer:
    """Evolves optimal strategy parameters using a simple genetic algorithm."""
    def __init__(self, param_ranges: Dict[str, Tuple[float, float]], pop_size: int = 20, generations: int = 10):
        self.ranges = param_ranges
        self.pop_size = pop_size
        self.generations = generations

    def evolve(self, fitness_func: Callable[[Dict], float]) -> Dict[str, float]:
        pop = [self._random_individual() for _ in range(self.pop_size)]
        best_ind = None
        best_fit = -np.inf

        for gen in range(self.generations):
            # Evaluate
            scores = [(ind, fitness_func(ind)) for ind in pop]
            scores.sort(key=lambda x: x[1], reverse=True)
            best_ind, best_fit = scores[0]
            logger.debug(f"Gen {gen}: Best Fitness = {best_fit:.4f}")

            # Selection & Crossover (Elitism + Random mix)
            new_pop = [best_ind] # Keep best
            while len(new_pop) < self.pop_size:
                p1 = random.choice(scores[:5])[0]
                p2 = random.choice(scores[:5])[0]
                child = self._crossover(p1, p2)
                child = self._mutate(child)
                new_pop.append(child)
            pop = new_pop

        return best_ind

    def _random_individual(self) -> Dict[str, float]:
        return {k: random.uniform(v[0], v[1]) for k, v in self.ranges.items()}

    def _crossover(self, p1: Dict, p2: Dict) -> Dict:
        return {k: (p1[k] + p2[k]) / 2 for k in self.ranges}

    def _mutate(self, ind: Dict, prob: float = 0.1) -> Dict:
        mutated = dict(ind)
        for k in mutated:
            if random.random() < prob:
                low, high = self.ranges[k]
                mutated[k] = random.uniform(low, high)
        return mutated
