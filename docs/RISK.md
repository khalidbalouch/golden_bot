# Golden Bot — Phase 7: Dynamic Risk & Portfolio Allocation
## Core Philosophy
**Survival > Profit.** Every trade passes multi-layer validation before execution. Position sizing adapts to volatility, regime, and model confidence. Portfolio allocation respects correlation caps and drawdown governors.
## Architecture
1. `RiskEngine`: Orchestrates per-trade limits, portfolio caps, kill switch, drawdown tracking
2. `PositionSizer`: Fractional Kelly + confidence/regime/vol modulators + hard bounds
3. `PortfolioAllocator`: Equal, Risk Parity, Conviction-Weighted modes with rebalancing thresholds
4. `CorrelationTracker`: Rolling covariance, sector exposure monitoring, concentration alerts
5. `VolatilityEstimator`: EMA-smoothed realized vol, regime classification, forward forecast
6. `RiskMetricsCalculator`: Sharpe, Sortino, Calmar, VaR, ES, Risk-of-Ruin
## Rate Limit & Compute Compliance
- All risk math is CPU-bound vectorized operations
- Zero REST/WebSocket calls
- Updates on every trade signal or WS market update
## Operational Notes
- Start with Conservative profile; upgrade after 30 days positive EV
- Kill switch is HARD: requires manual `reset_halt()` call
- Calibrate Kelly coefficient monthly via `scripts/calibrate_kelly.py`
- Never set fractional_kelly_coeff > 0.5 (overbetting leads to ruin)
