#!/usr/bin/env python3
"""
scripts/collect_data.py — Phase 2: Collect Historical Data for ML Training
Self-contained. No broken imports. Works on Windows/Linux/Mac.
"""
import asyncio
import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from core.data_pipeline import DataIngestionEngine, DataConfig
from core.security import BotConfig


def load_bot_config() -> BotConfig:
    """Load BotConfig from .env + defaults."""
    config_dict = {}
    profile_path = Path("config/profiles/standard.json")
    if profile_path.exists():
        with open(profile_path, encoding="utf-8") as f:
            config_dict.update(json.load(f))

    for key, value in os.environ.items():
        if key.startswith("GOLDEN_BOT_"):
            config_key = key[11:].lower()
            if config_key == "watchlist" and isinstance(value, str):
                config_dict[config_key] = [s.strip().upper() for s in value.split(",") if s.strip()]
            else:
                config_dict[config_key] = value

    return BotConfig(**config_dict)


async def main():
    parser = argparse.ArgumentParser(description="Collect historical data for ML training")
    parser.add_argument("--symbol", "-s", type=str, help="Trading pair (e.g., BTCUSDT)")
    parser.add_argument("--timeframe", "-t", type=str, default="15m", help="Candle interval (default: 15m)")
    parser.add_argument("--start", type=str, help="Start date YYYY-MM-DD (default: 90 days ago)")
    parser.add_argument("--end", type=str, help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--output", "-o", type=str, help="Output directory (default: data/training)")
    parser.add_argument("--env", "-e", type=str, help="Environment: testnet or live (default: from .env)")

    args = parser.parse_args()

    # Load defaults from .env
    bot_config = load_bot_config()

    symbol = (args.symbol or bot_config.watchlist[0] or "BTCUSDT").upper()
    timeframe = args.timeframe or bot_config.default_timeframe or "15m"
    env = args.env or bot_config.env or "testnet"
    output_dir = args.output or "data/training"

    end_date = args.end or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start or (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    # Clear Logging Header
    print(f"""
╔════════════════════════════════════════════════════════════════════════╗
║  🤖 GOLDEN BOT — DATA COLLECTION (Phase 2)                            ║
╠════════════════════════════════════════════════════════════════════════╣
║  Symbol:     {symbol:<12}                                           ║
║  Timeframe:  {timeframe:<12}                                          ║
║  Environment: {env:<12}                                          ║
║  Date Range: {start_date} to {end_date}                  ║
║  Output:     {output_dir}                                  ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    data_config = DataConfig(
        symbol=symbol,
        timeframe=timeframe,
        env=env,
        data_dir=output_dir,
    )

    engine = DataIngestionEngine(config=data_config)
    await engine.start()

    print(f"📥 Fetching {symbol} {timeframe} data from Binance {env}...")
    print(f"   This may take 2-5 minutes depending on date range.\n")

    try:
        df = await engine.fetch_historical_range(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            batch_size=1000,
        )

        if df.empty:
            print("❌ No data fetched. Check symbol, timeframe, and network connectivity.")
            return

        # Generate features
        print(f"🔧 Generating features for {symbol}...")
        from core.features import generate_features
        df_features = generate_features(df, symbol)

        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"{symbol}_{timeframe}_{timestamp}_features.parquet"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df_features.to_parquet(output_file, compression="snappy")

        # Summary
        feature_count = len(
            [c for c in df_features.columns if c not in ['target_return_15m', 'target_direction', 'symbol']])
        print(f"""
╔════════════════════════════════════════════════════════════════════════╗
║  ✅ DATA COLLECTION COMPLETE                                           ║
╠════════════════════════════════════════════════════════════════════════╣
║  Symbol:        {symbol}                                          ║
║  Timeframe:     {timeframe}                                         ║
║  Candles:       {len(df):>6,}                                       ║
║  Features:      {feature_count:>6,}                                      ║
║  Date Range:    {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}  ║
║  Quality Score: {df_features.attrs.get('quality_score', 0):.3f}                                      ║
║  Output File:   {output_file} ║
╚════════════════════════════════════════════════════════════════════════╝
        """)

        print("🎯 Next: Train your ML model")
        print(f"   python scripts/train_model.py --input \"{output_file}\" --symbol {symbol}")

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())d