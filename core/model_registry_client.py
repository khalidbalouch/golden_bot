from __future__ import annotations
import logging
import os
from typing import Any, Dict, Optional, List
import mlflow
import mlflow.sklearn
import pandas as pd

logger = logging.getLogger("golden_bot.orchestration.model_registry")

class ModelRegistryClient:
    """MLflow integration for experiment tracking, model versioning & lifecycle."""
    def __init__(self, tracking_uri: str = "http://localhost:5000", experiment_name: str = "golden_bot_ml"):
        mlflow.set_tracking_uri(tracking_uri)
        self.experiment_id = mlflow.set_experiment(experiment_name).experiment_id

    def log_model(self, model: Any, model_name: str, metrics: Dict[str, float], 
                  params: Dict[str, Any] = None, tags: Dict[str, str] = None) -> str:
        with mlflow.start_run(experiment_id=self.experiment_id, run_name=model_name) as run:
            if params:
                mlflow.log_params(params)
            if metrics:
                mlflow.log_metrics(metrics)
            if tags:
                mlflow.set_tags(tags)
            mlflow.sklearn.log_model(model, artifact_path="model")
            logger.info(f"📦 Logged model {model_name} run_id={run.info.run_id}")
        return run.info.run_id

    def promote_to_production(self, run_id: str, model_name: str) -> None:
        client = mlflow.MlflowClient()
        client.transition_model_version_stage(
            name=model_name, version=1, stage="Production", archive_existing_versions=True
        )
        logger.info(f"🚀 Promoted {model_name} run_id={run_id} to Production")

    def load_production_model(self, model_name: str) -> Any:
        client = mlflow.MlflowClient()
        versions = client.get_latest_versions(model_name, stages=["Production"])
        if not versions:
            raise RuntimeError(f"No production version for {model_name}")
        model_uri = f"models:/{model_name}/{versions[0].version}"
        logger.info(f"📥 Loading production model: {model_uri}")
        return mlflow.sklearn.load_model(model_uri)

    def compare_models(self, run_ids: List[str], metrics: List[str]) -> pd.DataFrame:
        client = mlflow.MlflowClient()
        rows = []
        for rid in run_ids:
            run = client.get_run(rid)
            row = {"run_id": rid, **{m: run.data.metrics.get(m, 0) for m in metrics}}
            rows.append(row)
        return pd.DataFrame(rows)
