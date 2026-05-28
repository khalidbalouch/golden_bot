# Golden Bot — Phase 19: Market Making & Liquidity Provision
## Core Philosophy
**Yield Generation via Spreads.** While the Alpha engine (Phases 1-18) captures directional trends, the Market Making (MM) engine captures bid-ask spreads and maker rebates.
## Architecture
1. **Avellaneda-Stoikov Model**: Theoretical foundation for optimal bid/ask pricing based on inventory risk.
2. **Inventory Manager**: Tracks open positions and applies skew to discourage over-exposure.
3. **Spread Optimizer**: Dynamically adjusts spread width based on volatility and exchange fee tiers.
4. **MM Engine**: Orchestrates data feeds, pricing, and order updates.
## Configuration
- `risk_aversion` (gamma): Higher = tighter spreads, less inventory risk.
- `base_spread_bps`: Target spread in basis points.
- `maker_rebate`: Exchange rebate for maker orders (e.g., 0.0002).
## Usage
1. `python scripts/run_mm_mode.py`
2. Ensure bot is configured with `maker` fee tier for rebates.
## Integration Notes
- Runs parallel to Alpha Engine.
- Uses separate risk bucket defined in `max_inventory`.
- Orders are submitted via Phase 3 ExecutionEngine with `reduce_only=False` but monitored for skew.
