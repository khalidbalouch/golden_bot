#!/usr/bin/env python3
"""CLI: Historical data downloader for Golden Bot"""
import argparse
import logging
import sys
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(message)s')

def main(symbols: str, start: str, end: str, output: str = "data_raw"):
    syms = [s.strip() for s in symbols.split(",")]
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    for sym in syms:
        logger = logging.getLogger(f"backfill.{sym}")
        logger.info(f"📥 Downloading {sym} from {start} to {end}")
        # Simulated backfill output
        df = pd.DataFrame({
            "timestamp": pd.date_range(start, end, freq="15min").astype(int)//10**6,
            "open": [1.0]*100, "high": [1.1]*100, "low": [0.95]*100, "close": [1.05]*100, "volume": [100.0]*100
        })
        df.to_parquet(out / f"{sym}_15m.parquet", index=False)
        logger.info(f"✅ Saved {len(df)} candles to {out / f'{sym}_15m.parquet'}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", required=True)
    p.add_argument("--start", default="2024-01-01")
    p.add_argument("--end", default="2024-12-31")
    p.add_argument("--output", default="data_raw")
    args = p.parse_args()
    main(args.symbols, args.start, args.end, args.output)
