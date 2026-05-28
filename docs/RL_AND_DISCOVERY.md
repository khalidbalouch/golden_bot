# Golden Bot — Phase 13: Reinforcement Learning & Automated Strategy Discovery
## Core Philosophy
**Adaptive Intelligence > Static Rules.** RL learns optimal execution & sizing from market feedback. 
Strategy discovery mines novel alpha formulas and optimal parameters automatically.
## Architecture
1. `CryptoTradingEnv`: Gymnasium-compliant environment simulating trading with slippage/fees.
2. `PPOAgent`: Proximal Policy Optimization agent with Actor-Critic network.
3. `EWCOnlineLearner`: Prevents catastrophic forgetting during live adaptation.
4. `GeneticStrategyOptimizer`: DEAP-based evolution of strategy parameters.
5. `AlphaSymbolicMiner`: GPlearn-based symbolic regression for interpretable alpha mining.
6. `NASController`: Neural Architecture Search for optimal model topologies.
## Training Workflow
1. Prepare data: `python scripts/train_rl_agent.py --data market.csv`
2. Evolve params: `python scripts/evolve_strategies.py --generations 50`
3. Mine alpha: `python scripts/mine_symbolic_alpha.py --data features.csv`
## Integration Notes
- RL agent outputs actions [0: Hold, 1: Buy, 2: Sell] consumed by Phase 3 Execution.
- Discovered formulas injected into Phase 4 FeaturePipeline.
- EWC ensures live updates don't destroy pre-trained knowledge.
## Rate Limit Compliance
- Training runs offline on historical data (CSV/Parquet).
- Online learning updates are batched & throttled to respect compute limits.
