"""
ml/inference.py — Real-time signal generation with trained model
"""
import joblib
import pandas as pd
import numpy as np
from core.features import generate_features


class SignalGenerator:
    def __init__(self, model_path: str, symbol: str, threshold: float = 0.6):
        self.model = joblib.load(model_path)
        self.symbol = symbol
        self.threshold = threshold  # Probability threshold for signal
        self.feature_cols = self.model.feature_names if hasattr(self.model, 'feature_names') else None

    def generate_signal(self, df: pd.DataFrame) -> dict:
        """Generate trading signal from latest data."""
        # Generate features for latest candle
        df_features = generate_features(df.tail(100).copy(), self.symbol)  # Need history for indicators

        if df_features.empty or self.feature_cols is None:
            return {"signal": "HOLD", "confidence": 0.0, "reason": "Insufficient data"}

        # Prepare input (ensure all features present)
        X = df_features[self.feature_cols].tail(1)

        # Predict
        prob_up = self.model.predict_proba(X)[0, 1]
        prediction = self.model.predict(X)[0]

        # Generate signal with confidence
        if prob_up >= self.threshold:
            signal = "BUY"
            confidence = prob_up
        elif prob_up <= (1 - self.threshold):
            signal = "SELL"
            confidence = 1 - prob_up
        else:
            signal = "HOLD"
            confidence = 0.5

        return {
            "signal": signal,
            "confidence": round(confidence, 3),
            "prob_up": round(prob_up, 3),
            "timestamp": df_features.index[-1],
            "top_features": self._get_top_features(X)
        }

    def _get_top_features(self, X: pd.DataFrame) -> dict:
        """Return top 3 contributing features for this prediction."""
        if not hasattr(self.model, 'feature_importances_'):
            return {}
        importance = pd.Series(self.model.feature_importances_, index=self.feature_cols)
        top_idx = importance.nlargest(3).index
        return {feat: round(X[feat].iloc[0], 4) for feat in top_idx if feat in X.columns}