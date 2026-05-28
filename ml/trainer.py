"""
ml/trainer.py — Train, validate, and deploy ML models
"""
import pandas as pd
import numpy as np
import joblib
import mlflow
import mlflow.xgboost
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from xgboost import XGBClassifier
from pathlib import Path


class ModelTrainer:
    def __init__(self, symbol: str, model_dir: str = "models"):
        self.symbol = symbol
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        mlflow.set_experiment(f"golden_bot_{symbol}")

    def load_data(self, feature_file: str) -> pd.DataFrame:
        """Load pre-computed features."""
        return pd.read_parquet(feature_file)

    def prepare_data(self, df: pd.DataFrame, test_ratio: float = 0.2):
        """Prepare train/test splits with time-series awareness."""
        # Features (exclude target and metadata)
        feature_cols = [c for c in df.columns if c not in ['target', 'target_direction', 'symbol']]
        X = df[feature_cols]
        y = df['target_direction']  # Binary: 1=up, 0=down

        # Time-series split: last 20% for testing
        split_idx = int(len(df) * (1 - test_ratio))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        return X_train, X_test, y_train, y_test, feature_cols

    def train_xgboost(self, X_train, y_train, X_test, y_test, feature_cols):
        """Train XGBoost classifier with hyperparameter tuning."""
        with mlflow.start_run(run_name=f"xgb_{self.symbol}"):
            # Log parameters
            mlflow.log_params({
                "model": "xgboost",
                "symbol": self.symbol,
                "features": len(feature_cols)
            })

            # Model with conservative settings (avoid overfitting)
            model = XGBClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),  # Handle imbalance
                random_state=42,
                eval_metric='logloss',
                use_label_encoder=False
            )

            # Train with early stopping
            model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                early_stopping_rounds=20,
                verbose=False
            )

            # Evaluate
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            # Log metrics
            mlflow.log_metrics({
                "accuracy": (y_pred == y_test).mean(),
                "roc_auc": roc_auc_score(y_test, y_proba),
                "precision": classification_report(y_test, y_pred, output_dict=True)['1']['precision'],
                "recall": classification_report(y_test, y_pred, output_dict=True)['1']['recall'],
                "f1": classification_report(y_test, y_pred, output_dict=True)['1']['f1-score']
            })

            # Log feature importance
            importance = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
            mlflow.log_dict(importance.head(20).to_dict(), "top_features.json")

            # Save model
            model_path = self.model_dir / f"{self.symbol}_xgb_model.joblib"
            joblib.dump(model, model_path)
            mlflow.sklearn.log_model(model, "model")

            print(
                f"✅ Model trained: AUC={roc_auc_score(y_test, y_proba):.3f}, F1={classification_report(y_test, y_pred, output_dict=True)['1']['f1-score']:.3f}")
            return model, model_path

    def walk_forward_validation(self, df: pd.DataFrame, n_splits: int = 5):
        """Walk-forward validation for time-series robustness."""
        tscv = TimeSeriesSplit(n_splits=n_splits)
        feature_cols = [c for c in df.columns if c not in ['target', 'target_direction', 'symbol']]
        X = df[feature_cols]
        y = df['target_direction']

        scores = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            model = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, use_label_encoder=False)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            scores.append(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))

        print(f"📊 Walk-forward AUC: {np.mean(scores):.3f} ± {np.std(scores):.3f}")
        return np.mean(scores)