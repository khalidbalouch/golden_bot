from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Literal, Dict, Optional
from sklearn.ensemble import IsolationForest

logger = logging.getLogger("golden_bot.anomaly")

@dataclass
class AnomalyReport:
    timestamp: int
    score: float
    anomaly_type: Literal["corruption", "feed_disruption", "exchange_glitch", "spoofing"]
    severity: Literal["low", "medium", "high"]
    suggested_action: str

class MultiDimensionalAnomalyDetector:
    def __init__(self, detection_methods: List[Literal["isolation_forest", "autoencoder", "zscore"]] = None):
        self.methods = detection_methods or ["isolation_forest", "zscore"]
        self.model = None

    def fit(self, training_data: pd.DataFrame) -> None:
        numeric = training_data.select_dtypes(include="number").fillna(0)
        if "isolation_forest" in self.methods:
            self.model = IsolationForest(contamination=0.05, random_state=42).fit(numeric)
        logger.info(f"✅ Anomaly detector fitted with methods: {self.methods}")

    def detect_anomalies(self, current_data: pd.DataFrame) -> List[AnomalyReport]:
        reports = []
        numeric = current_data.select_dtypes(include="number").fillna(0)
        if self.model:
            scores = self.model.decision_function(numeric)
            for idx, score in enumerate(scores):
                if score < -0.2:
                    reports.append(AnomalyReport(
                        timestamp=int(current_data.index[idx]) if isinstance(current_data.index, pd.RangeIndex) else idx,
                        score=abs(score),
                        anomaly_type="feed_disruption",
                        severity="high" if score < -0.5 else "medium",
                        suggested_action="switch to backup feed" if score < -0.5 else "flag & continue"
                    ))
        return reports

    def handle_anomaly(self, report: AnomalyReport) -> str:
        if report.severity == "low": return "log_and_continue"
        if report.severity == "medium": return "impute_with_uncertainty"
        return "pause_and_alert"
