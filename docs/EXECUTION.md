# Golden Bot — Phase 3: Live Execution & Rate-Limited Routing
## Core Philosophy
**WS-first, REST-minimal.** Binance rate limits are strict (2400 req/min IP, 60 orders/10s). 
Phase 3 enforces compliance via:
- `BinanceRateLimiter`: Async token-bucket + sliding window with auto-queue
- `BinanceWSManager`: Real-time order updates, depth, balance (zero polling)
- Header sync: Parses `x-mbx-used-weight-1m` to stay in lockstep
- Circuit Breaker: Auto-halts on consecutive failures, recovers gracefully
## Architecture
1. `ExecutionEngine` orchestrates `SmartOrderRouter`
2. Router checks `BinanceRateLimiter.acquire()` before any outbound call
3. WS streams push execution reports → `PartialFillReconciler` updates state
4. REST used ONLY for order submission/cancellation
5. State machine enforces valid transitions, audit logs all actions
## Rate Limit Strategy
- IP Limit: 1200 req/min (conservative default)
- Order Limit: 50 orders/10s
- Auto-queue: Requests wait if limits approached
- WS fallback: Status checks use WS cache first
## Testing
Run: `cd golden_bot && python scripts/test_execution_flow.py`
Run tests: `pytest tests/execution/ -v`
