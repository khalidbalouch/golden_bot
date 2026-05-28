# Golden Bot — Phase 6: Backtesting & Stress Testing
## Core Philosophy
**Realistic Simulation > Optimistic Backtests.** Every fill accounts for latency, queue position, market impact, fees, and funding.
## Architecture
1. `BacktestEngine`: Chronological signal processing, state machine tracking, PnL curve generation
2. `WalkForwardValidator`: Non-overlapping folds, strict parameter locking, out-of-sample robustness
3. `MonteCarloSimulator`: Block shuffling, parameter perturbation, ruin probability estimation
4. `LatencySimulator` & `MarketImpact`: Queue modeling, square-root impact slippage
5. `PortfolioBacktester`: Correlation-aware margin, sector exposure limits, multi-symbol sync
6. `StressTester`: Volatility spikes, liquidity droughts, exchange outage injection
## Rate Limit & Compute Compliance
- 100% offline. Zero REST/WebSocket calls during backtesting
- Uses pre-loaded CSV/Parquet market data
- CPU-optimized for vectorized operations
## Usage
1. `python scripts/run_backtest.py --data market_data.csv`
2. `python scripts/analyze_results.py --trades trades.csv --scenarios 1000`
3. `pytest tests/backtest/ -v`
## Operational Notes
- Always use walk-forward validation before live deployment
- Monte Carlo P10 drawdown must be <20% for production approval
- Stress test max DD must not exceed risk limits (e.g., 15%)
