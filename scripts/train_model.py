# Create training script: scripts/train_model.py
"""
scripts/train_model.py — Train XGBoost model for signal generation
"""
import asyncio
import sys
import joblib
import mlflow
import mlflow.xgboost
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd


async def main():
    # Load features
    data_path = Path("data/training/BTCUSDT_15m_features.parquet")
    if not data_path.exists():
        print("❌ Run collect_data.py first")
        return
    df = pd.read_parquet(data_path)

    # Prepare features/target
    feature_cols = [c for c in df.columns if
                    c not in ["target_return_15m", "target_direction", "target_up_strong", "target_down_strong",
                              "symbol"]]
    X = df[feature_cols].dropna()
    y = df.loc[X.index, "target_direction"]  # Binary: 1=up, 0=down

    # Time-series split (no lookahead)
    tscv = TimeSeriesSplit(n_splits=5)

    # MLflow tracking
    mlflow.set_experiment("golden_bot_btcusdt_15m")

    best_score = 0
    best_model = None

    with mlflow.start_run(run_name="xgb_baseline"):
        # Log params
        mlflow.log_params({
            "model": "xgboost",
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "features": len(feature_cols),
            "samples": len(X)
        })

        # Walk-forward validation
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            # Handle class imbalance
            scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

            model = XGBClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=scale_pos_weight,
                random_state=42 + fold,
                eval_metric="logloss",
                use_label_encoder=False
            )

            model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                early_stopping_rounds=20,
                verbose=False
            )

            # Evaluate
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, y_proba)

            print(f"📊 Fold {fold + 1}: AUC={auc:.3f}")
            mlflow.log_metrics({f"fold_{fold + 1}_auc": auc})

            if auc > best_score:
                best_score = auc
                best_model = model

        # Log final metrics
        mlflow.log_metrics({
            "best_auc": best_score,
            "n_features": len(feature_cols),
            "n_samples": len(X)
        })

        # Save model
        model_path = Path("models/BTCUSDT_xgb_15m.joblib")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(best_model, model_path)
        mlflow.sklearn.log_model(best_model, "model")

        # Feature importance
        importance = pd.Series(best_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
        print("🔑 Top 10 features:")
        print(importance.head(10))
        mlflow.log_dict(importance.head(20).to_dict(), "top_features.json")

        print(f"✅ Model trained: Best AUC={best_score:.3f}, saved to {model_path}")


if __name__ == "__main__":
    asyncio.run(main())