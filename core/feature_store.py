from __future__ import annotations
import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Literal
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger("golden_bot.feature_store")

@dataclass
class FeatureSpec:
    name: str
    computation_fn: Callable[[pd.DataFrame], pd.Series]
    window_size: int
    dependencies: List[str] = field(default_factory=list)
    normalization: Optional[Literal["zscore", "minmax", "robust"]] = None

@dataclass
class DatasetVersion:
    version_tag: str
    feature_checksums: Dict[str, str]
    created_at: float
    source_code_hash: str

class FeatureStore:
    def __init__(self, storage_path: str = "feature_store", versioning_enabled: bool = True):
        self.storage = Path(storage_path)
        self.storage.mkdir(parents=True, exist_ok=True)
        self.versioning = versioning_enabled
        self._metadata: Dict[str, DatasetVersion] = {}
        self._load_versions()

    def compute_features(self, candles: pd.DataFrame, specs: List[FeatureSpec]) -> pd.DataFrame:
        df = candles.copy()
        for spec in specs:
            if not set(spec.dependencies).issubset(df.columns):
                raise ValueError(f"Missing dependencies for {spec.name}: {spec.dependencies}")
            df[spec.name] = spec.computation_fn(df)
            if spec.normalization == "zscore":
                m, s = df[spec.name].mean(), df[spec.name].std()
                df[spec.name] = (df[spec.name] - m) / (s + 1e-9)
        return df

    def get_point_in_time_snapshot(self, symbol: str, timestamp: int, feature_names: List[str]) -> Dict[str, Any]:
        path = self.storage / symbol / "data.parquet"
        if not path.exists(): return {}
        table = pq.read_table(path, columns=feature_names + ["timestamp"])
        df = table.to_pandas()
        mask = df["timestamp"] <= timestamp
        return df[mask].iloc[-1:].to_dict(orient="records")[0] if mask.any() else {}

    def register_version(self, version_tag: str, specs: List[FeatureSpec]) -> None:
        checksums = {s.name: self._hash_func(s.computation_fn) for s in specs}
        ver = DatasetVersion(version_tag, checksums, pd.Timestamp.now().timestamp(), self._hash_func(self.compute_features))
        self._metadata[version_tag] = ver
        (self.storage / f"{version_tag}.meta.json").write_text(json.dumps(ver.__dict__, indent=2))
        logger.info(f"📦 Registered feature version: {version_tag}")

    def load_features_by_version(self, symbol: str, version_tag: str) -> pd.DataFrame:
        if version_tag not in self._metadata: raise ValueError(f"Unknown version: {version_tag}")
        return pq.read_table(self.storage / symbol / "data.parquet").to_pandas()

    def _load_versions(self) -> None:
        for f in self.storage.glob("*.meta.json"):
            try:
                d = json.loads(f.read_text())
                self._metadata[d["version_tag"]] = DatasetVersion(**d)
            except: pass

    @staticmethod
    def _hash_func(fn: Callable) -> str:
        return hashlib.sha256(fn.__code__.co_code).hexdigest()[:16]
