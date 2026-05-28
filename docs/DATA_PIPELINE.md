# Golden Bot — Phase 2: Data Pipeline & Intelligence
## Overview
Enterprise-grade ingestion, validation, feature storage, and advanced data intelligence.
## Quick Start
1. Install deps: `pip install -r requirements_phase_2.txt`
2. Backfill: `python scripts/backfill_data.py --symbols BTCUSDT,ETHUSDT`
3. Validate: `python scripts/validate_features.py --symbol BTCUSDT --version v1`
4. Generate stress data: `python scripts/generate_synthetic_data.py --size 50000`
## Architecture
- Dual-source ingestion with automatic fallback
- Point-in-time correct feature store (Parquet)
- Regime-balanced synthetic generation
- Immutable DAG lineage tracking
- IsolationForest + counterfactual drift explanation
## Operational Notes
- Clock drift >100ms pauses ingestion automatically
- Quality score <0.95 triggers ops alert
- Lineage graph exported to `data/lineage/graph.json`
