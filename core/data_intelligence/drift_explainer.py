from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

logger = logging.getLogger("golden_bot.drift")

@dataclass
class DriftExplanation:
    feature: str
    shift_magnitude: float
    direction: Literal["increase", "decrease", "distribution_change"]
    top_contributors: List[str]

@dataclass
class ProbableCause:
    cause: str
    confidence: float
    remediation: str

class DriftExplainer:
    def __init__(self, reference_data: pd.DataFrame, explanation_method: Literal["shap", "counterfactual"] = "counterfactual"):
        self.ref_means = reference_data.select_dtypes(include="number").mean()
        self.ref_std = reference_data.select_dtypes(include="number").std()
        self.method = explanation_method

    def explain_drift(self, current_data: pd.DataFrame) -> List[DriftExplanation]:
        explanations = []
        cur_means = current_data.select_dtypes(include="number").mean()
        cur_std = current_data.select_dtypes(include="number").std()
        for col in self.ref_means.index:
            shift = abs((cur_means.get(col, 0) - self.ref_means.get(col, 0)) / (self.ref_std.get(col, 1) + 1e-9))
            if shift > 1.0:
                explanations.append(DriftExplanation(
                    feature=col,
                    shift_magnitude=shift,
                    direction="increase" if cur_means[col] > self.ref_means[col] else "decrease",
                    top_contributors=[col]
                ))
        return explanations

    def map_to_root_cause(self, explanation: DriftExplanation) -> ProbableCause:
        if explanation.shift_magnitude > 3.0: return ProbableCause("feed_provider_change", 0.85, "switch data source")
        if "volume" in explanation.feature.lower(): return ProbableCause("exchange_api_update", 0.7, "check exchange docs")
        return ProbableCause("macro_regime_shift", 0.6, "retrain model")

    def generate_remediation_report(self, explanation: DriftExplanation, cause: ProbableCause) -> Dict[str, str]:
        return {
            "feature": explanation.feature,
            "cause": cause.cause,
            "action": cause.remediation,
            "confidence": f"{cause.confidence:.2f}",
            "impact": "retrain_model" if cause.confidence > 0.7 else "monitor"
        }
