#!/usr/bin/env python3
"""CLI: Stress-test dataset generator"""
import argparse
import logging
import sys
from pathlib import Path
from core.data_intelligence.synthetic_generator import SyntheticMarketGenerator
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(message)s')

def main(regimes: str, size: int, output: str):
    # Mock base data for generation
    base = pd.DataFrame({"open":[1,2],"high":[1.1,2.2],"low":[0.9,1.8],"close":[1.05,2.05],"volume":[100,200]})
    regs = pd.Series(["TREND","CHOP"])
    gen = SyntheticMarketGenerator(base, regs)
    gen.train_generative_model()
    dist = {r: 1/len(regimes.split(",")) for r in regimes.split(",")}
    synth = gen.generate_synthetic_dataset(size, dist)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    synth.to_parquet(out / "synthetic.parquet", index=False)
    logging.info(f"✅ Saved {len(synth)} synthetic rows to {out / 'synthetic.parquet'}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--regimes", default="TREND,CHOP")
    p.add_argument("--size", type=int, default=10000)
    p.add_argument("--output", default="data_raw/synthetic")
    args = p.parse_args()
    main(args.regimes, args.size, args.output)
