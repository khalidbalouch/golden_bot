# Golden Bot — Phase 8: Advanced Trade Management & Adaptive Exits
## Core Philosophy
**Manage the trade, not just the entry.** Scale with conviction, exit with intelligence, and respect market liquidity.
## Architecture
1. `TradeManager`: State machine orchestrator, listens to WS updates, routes to scale/exit engines
2. `ScaleLogic`: Conviction tracking (EMA), pullback validation, fractional size addition
3. `ExitEngine`: Priority resolver (Hard SL > TP Ladder > Trailing > Time Decay)
4. `TrailingStop`: Chandelier + ATR multiplier, hard SL override, activation threshold
5. `TPLadder`: Multi-target allocation, dynamic redistribution on early fills
6. `TimeDecayExit`: Exponential edge decay, max duration governor
7. `LiquidityAwareExecutor`: Order pacing, slippage estimation, limit/market routing logic
## Integration Notes
- Connects to Phase 3 `ExecutionEngine` for order placement
- Consumes Phase 4 `FeaturePipeline` for live conviction/probability feeds
- Respects Phase 7 `RiskEngine` sizing limits & correlation caps
## Rate Limit Compliance
- All logic runs on local state & WS price pushes
- Zero REST polling during trade management
- Orders batched via Phase 3 rate limiter
## Usage
1. Configure: `config/exit_strategies/*.json`
2. Optimize: `python scripts/optimize_exit_params.py --data backtest.csv`
3. Simulate scales: `python scripts/simulate_scale_logic.py --conviction signals.csv`
4. Tests: `pytest tests/trade_management/ -v`
## Operational Rules
- Never scale against a losing position
- Trailing stop activates only after TP1 or breakeven
- Time decay forces exit if edge decays >70% and PnL < threshold
- Liquidity pacing prevents market orders during low-depth/high-vol regimes
