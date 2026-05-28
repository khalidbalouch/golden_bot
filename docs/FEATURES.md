# Golden Bot — Phase 4: Advanced Feature Engineering & Dashboard
## Core Philosophy
**WS-Only Alpha Computation.** Zero REST polling for feature generation. 
Streams trade, depth, mark price, and funding events to compute microstructure & derivative features in real-time.
## Architecture
1. `BinanceWSManager` pushes raw market events
2. `FeaturePipeline` increments buffers & computes: CVD, Orderbook Imbalance, Spread Bps, VPIN, Funding Alpha, OI Momentum, LiQ Proximity
3. `FeatureStore` caches point-in-time correct snapshots
4. `Dashboard` & `WebMonitor` pull latest features for live alpha visualization
## Rate Limit Compliance
- Features computed purely from WS push events
- REST endpoints untouched during feature generation
- Dashboard/Web UI use SSE/async refresh, zero polling overhead
## Dashboard
- Terminal: Rich Live layout with Account, Alpha/Microstructure, Trades, Regimes, Log
- Web: Flask + SSE real-time sync, token auth, dark-theme professional UI
Run: `cd golden_bot && python utils/web_monitor.py` (auto-started by engine)
