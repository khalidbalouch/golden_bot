# Golden Bot — Phase 15: Macro, Options & Liquidity Toxicity
## Core Philosophy
**Context is King.** A signal is not enough. You must know *when* to trade (Macro) and *who* is trading against you (Toxicity/GEX).
## Architecture
1. `MacroCorrelator`: Live tracking of DXY/SPX/Bond correlations with crypto assets.
2. `EventProcessor`: Economic calendar integration; reduces risk exposure before FOMC/CPI.
3. `VolatilitySurface`: IV reconstruction and 25-Delta Skew calculation.
4. `GammaExposure`: Calculates GEX and "Max Pain" levels to predict volatility suppression/amplification.
5. `VPINEstimator`: Volume-Synchronized Probability of Informed Trading to detect toxic order flow.
6. `MacroOrchestrator`: Central hub aggregating all external signals into a `risk_multiplier`.
## Usage
1. `python scripts/scan_macro.py` - Test macro correlations & VPIN.
2. `python scripts/calc_gex.py` - Test Gamma Exposure & Max Pain.
3. `pytest tests/ml/test_phase15.py`
## Integration Notes
- `risk_multiplier` from `MacroOrchestrator` feeds directly into Phase 7 `PositionSizer`.
- `toxicity_alert` from `VPINEstimator` pauses execution in Phase 3 `ExecutionEngine`.
- `Gamma Flip` levels from `GammaExposure` act as dynamic Support/Resistance in Phase 14 `FractalAnalyzer`.
