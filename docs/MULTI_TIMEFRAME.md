# Golden Bot — Phase 14: Multi-Timeframe Intelligence & Graph Relations
## Core Philosophy
**Top-Down Validation.** Never trade against the Higher Timeframe (HTF). Use fractal synchronization to confirm market structure.
## Architecture
1. `HierarchicalFusionEngine`: Propagates HTF bias down to LTF. Weights HTF heavily in trending markets.
2. `FractalAnalyzer`: Computes Higuchi Fractal Dimension to detect regime shifts & trend persistence.
3. `AlignmentScorer`: Scores HTF/LTF agreement. Penalizes leverage when timeframes conflict.
4. `TimeframeVotingSystem`: Regime-adaptive weighted voting across all selected timeframes.
5. `RelationalAttentionLayer`: PyTorch module for learning dynamic cross-asset dependencies.
6. `MultiTFDecisionEngine`: Orchestrates all modules into a unified signal filter.
## Integration Notes
- Feeds `alignment.recommended_leverage_multiplier` into Phase 7 `PositionSizer`.
- Filters out low-consensus signals before Phase 3 `ExecutionEngine`.
- Graph attention outputs feed Phase 5 `EnsembleManager` as meta-features.
## Usage
1. Analyze: `python scripts/analyze_multiframe.py --symbol BTCUSDT`
2. Test Logic: `python scripts/test_alignment.py`
3. Validate: `pytest tests/ml/test_multiframe.py -v`
## Operational Rules
- If HTF is NEUTRAL, block LTF entries (prevents chop trading).
- Fractal sync < 0.5 indicates market structure breakdown → reduce position size by 50%.
- Voting consensus < 0.6 triggers `REVIEW` status, not `EXECUTE`.
