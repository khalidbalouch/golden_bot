# Golden Bot — Phase 5: Institutional ML Stack
## Architecture
- **Stacking Ensemble**: XGBoost + LightGBM base learners, LogisticRegression meta-learner
- **Meta-Labeler**: Filters low-EV signals post-ensemble, trained on fee-adjusted outcomes
- **Conformal Prediction**: Guarantees prediction interval coverage (e.g., 90%)
- **SHAP Interpreter**: Live feature attribution, drift detection via importance shift
- **Drift Monitor**: PSI for feature distribution, ADWIN-like window split for concept drift
- **Sequence Models**: PyTorch LSTM & causal-masked Transformer for temporal orderflow
- **Regime Router**: GMM-based regime classification, routes to regime-specific models
- **Lifecycle Manager**: Versioning, shadow validation, atomic promotion, archival
- **Prediction Service**: Async API, caching, fallback routing, drift-aware cache invalidation
## Rate Limit & Compute Compliance
- ML inference runs offline or on batched WS features (Phase 4)
- Zero REST during training/prediction
- Torch models exported to ONNX for CPU/GPU routing
## Training Workflow
1. `python scripts/train_ensemble.py --data features.csv --target label`
2. `python scripts/validate_model.py --train train.csv --val val.csv --target label`
3. Deploy to `model_registry/`, activate via `PredictionService`
## Operational Notes
- Auto-retrain triggered when PSI > 0.2 or concept drift detected
- Shadow models run in parallel; promotion requires Sharpe > baseline + 0.2
- All models versioned with timestamps, metrics, and drift baselines
