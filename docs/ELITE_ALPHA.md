# Golden Bot — Phase 11: Elite Alpha Layers & Multi-Agent Intelligence
## Core Philosophy
**Adaptive, Cross-Market, Conflict-Resolved.** Elite alpha requires regime awareness, cross-exchange inefficiency capture, and multi-agent coordination to avoid self-sabotage.
## Architecture
1. `RegimeHMM`: Gaussian Mixture HMM for state classification + Bayesian structural break detection
2. `CrossExchangeAlpha`: Real-time basis arbitrage scanner, funding divergence tracker, liquidity migration detector
3. `CrossAssetGNNEncoder`: PyTorch Graph Attention Network for learning latent asset dependencies
4. `MultiAgentCoordinator`: Priority-weighted conflict resolution (Risk > Execution > Signal) with veto power
5. `ElasticWeightConsolidation`: Continual learning module preventing catastrophic forgetting during online updates
6. `AlphaOrchestrator`: Central router aggregating HMM state, cross-exchange signals, and agent decisions
7. `AutonomousResearchAgent`: Paper ingestion, hypothesis extraction, and experiment scheduling pipeline
8. `DynamicGraphBuilder`: Live correlation/flow graph construction for GNN input
## Rate Limit & Compute Compliance
- Cross-exchange alpha uses WS streams + lightweight HTTP polling (capped at 1 req/s)
- HMM & GNN run offline/batched; online inference uses pre-computed embeddings
- Multi-agent coordination runs in-memory, zero network overhead
## Integration Notes
- `AlphaOrchestrator` pushes validated signals to Phase 3 `ExecutionEngine`
- Regime states feed into Phase 5 `PredictionService` for model routing
- GNN embeddings augment Phase 4 `FeaturePipeline`
## Usage
1. Train HMM: `python scripts/train_regime_hmm.py --data features.csv`
2. Scan Alpha: `python scripts/scan_cross_exchange.py`
3. Simulate Agents: `python scripts/run_multi_agent_sim.py`
4. Tests: `pytest tests/ml/test_phase11.py -v`
## Operational Rules
- Arbitrage signals expire in <3s to avoid latency decay
- Risk agent veto overrides all other agents if confidence > 85%
- EWC lambda tuned monthly; reset on major regime shifts
- Research agent runs weekly; hypotheses require manual backtest validation before production
