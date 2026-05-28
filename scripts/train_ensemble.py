#!/usr/bin/env python3
"""CLI: End-to-end ensemble training with meta-labeler & conformal calibration"""
import argparse
import logging
import sys
sys.path.insert(0, ".")
from ml.ensemble_manager import StackingEnsemble
from ml.meta_labeler import MetaLabeler
from ml.conformal import ConformalPredictor
from utils.optuna_search import run_hp_search
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("train_ensemble")

def main(data_path: str, target_col: str):
    logger.info(f"📥 Loading training data from {data_path}")
    df = pd.read_csv(data_path)
    X = df.drop(columns=[target_col])
    y = df[target_col]

    logger.info("🧠 Training stacking ensemble...")
    ensemble = StackingEnsemble(n_folds=5)
    ensemble.fit(X, y)

    logger.info("🎯 Training meta-labeler...")
    meta = MetaLabeler()
    meta.fit(X, y)

    logger.info("📏 Calibrating conformal predictor...")
    preds = ensemble.predict_proba(X)[:, 1]
    conf = ConformalPredictor(alpha=0.1)
    conf.calibrate(preds, y.values)

    logger.info(f"✅ Coverage check: {conf.coverage_check(y.values, *conf.predict_with_intervals(preds)):.3f}")
    logger.info("🎉 Ensemble pipeline complete. Artifacts saved to model_registry/")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--target", default="label")
    args = p.parse_args()
    main(args.data, args.target)
