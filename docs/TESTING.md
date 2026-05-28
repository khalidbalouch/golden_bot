# Golden Bot — Testing & Resilience Framework
## Testing Pyramid
1. **Unit** (70%): Pure logic, state machines, risk math, feature computations
2. **Integration** (20%): WS → Feature → Risk → Execution → Dashboard pipeline
3. **Chaos/Performance** (10%): Fault injection, latency simulation, throughput benchmarks
## Execution
- Run all: `pytest golden_bot/tests/ -v`
- Chaos: `python scripts/run_chaos.py`
- Benchmarks: `python scripts/run_benchmarks.py`
## CI/CD Pipeline
- Triggers on PR → main
- Runs mypy, bandit, pytest-cov, Trivy container scan
- Blocks merge if coverage <90% or security scan fails
- Auto-builds & tags on main merge
