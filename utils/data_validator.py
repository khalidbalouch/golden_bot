from __future__ import annotations
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Tuple, Literal, Optional

logger = logging.getLogger("golden_bot.data_validator")

@dataclass
class CandleSchema:
    required_cols: List[str] = field(default_factory=lambda: ["timestamp","open","high","low","close","volume"])
    numeric_cols: List[str] = field(default_factory=lambda: ["open","high","low","close","volume"])

@dataclass
class GapInfo:
    start_ts: int; end_ts: int; expected_interval_ms: int; size: int

@dataclass
class QualityMetrics:
    completeness: float; continuity_score: float; outlier_ratio: float; overall_score: float

class DataValidator:
    def validate_schema(self, df: pd.DataFrame, schema: CandleSchema) -> pd.DataFrame:
        missing = [c for c in schema.required_cols if c not in df.columns]
        if missing: raise ValueError(f"Missing columns: {missing}")
        for c in schema.numeric_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        return df.dropna(subset=schema.required_cols)

    def detect_outliers(self, df: pd.DataFrame, col: str, method: Literal["iqr", "zscore"] = "iqr") -> List[int]:
        s = df[col].dropna()
        if method == "iqr":
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            return df[(s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)].index.tolist()
        else:
            z = np.abs((s - s.mean()) / (s.std() + 1e-9))
            return df[z > 3].index.tolist()

    def check_continuity(self, df: pd.DataFrame, expected_interval_ms: int) -> List[GapInfo]:
        gaps = []
        diffs = df["timestamp"].diff().dropna()
        for i, d in enumerate(diffs):
            if d > expected_interval_ms * 1.5:
                gaps.append(GapInfo(int(df.iloc[i-1]["timestamp"]), int(df.iloc[i]["timestamp"]), expected_interval_ms, int(d/expected_interval_ms)-1))
        return gaps
