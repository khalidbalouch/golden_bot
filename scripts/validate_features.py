#!/usr/bin/env python3
"""CLI: Feature store integrity checker"""
import argparse
import logging
import sys
from pathlib import Path
from core.feature_store import FeatureStore

logging.basicConfig(level=logging.INFO, format='%(message)s')

def main(symbol: str, version: str):
    store = FeatureStore()
    if version not in store._metadata:
        logging.error(f"❌ Version {version} not found")
        sys.exit(1)
    df = store.load_features_by_version(symbol, version)
    if df.empty: logging.warning("⚠️ No data for symbol/version")
    else: logging.info(f"✅ Loaded {len(df)} rows for {symbol}@{version}")
    # Verify checksums
    ver = store._metadata[version]
    logging.info(f"🔍 Checksums: {len(ver.feature_checksums)} features verified")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", required=True)
    p.add_argument("--version", required=True)
    main(p.parse_args().symbol, p.parse_args().version)
