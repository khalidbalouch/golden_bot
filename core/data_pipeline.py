"""
core/data_pipeline.py — Phase 2: Production Data Pipeline
Fetches, validates, repairs, and stores historical data for ML training.
Fixed: Correct handling of Timestamp Index in fetch loops.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import hmac
import hashlib
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
import requests  # For reliable Windows HTTP

from utils.data_validator import DataValidator, CandleSchema, QualityMetrics
from utils.gap_repair import GapRepairEngine, GapInfo, RepairStrategy

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","mod":"%(name)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("golden_bot.data_pipeline")


class GapRepairStrategy(Enum):
    LINEAR = "linear"
    FORWARD_FILL = "ffill"
    BACKUP_SOURCE = "backup"
    MARK_MISSING = "mark"


@dataclass
class DataConfig:
    primary_source: str = "binance_ws"
    backup_source: str = "binance_rest"
    divergence_threshold_pct: float = 0.001
    fallback_timeout_sec: int = 30
    max_gap_candles: int = 100
    quality_alert_threshold: float = 0.95
    data_dir: str = "data"
    symbol: str = "BTCUSDT"
    timeframe: str = "15m"
    env: str = "testnet"


@dataclass
class DataQualityScorer:
    def compute_quality_score(self, candles: pd.DataFrame) -> float:
        if candles.empty: return 0.0

        # 1. Continuity
        ts_diff = candles.index.to_series().diff().dropna()
        if len(ts_diff) == 0:
            continuity = 1.0
        else:
            expected = ts_diff.median()
            gaps = ts_diff[ts_diff > expected * 2]
            continuity = 1.0 - (len(gaps) / max(len(ts_diff), 1))

        # 2. OHLC consistency
        ohlc_ok = (
                (candles["high"] >= candles["low"]) &
                (candles["open"].between(candles["low"], candles["high"])) &
                (candles["close"].between(candles["low"], candles["high"]))
        )
        ohlc_consistency = ohlc_ok.mean()

        # 3. Volume & Outliers
        vol_ok = 1.0 - (candles["volume"] < 0).mean()

        if len(candles) >= 20:
            z = np.abs(
                (candles["close"] - candles["close"].rolling(20).mean()) / candles["close"].rolling(20).std().replace(0,
                                                                                                                      np.nan))
            outlier_ok = 1.0 - (z > 4).dropna().mean()
        else:
            outlier_ok = 1.0

        return max(0.0, min(1.0, 0.3 * continuity + 0.3 * ohlc_consistency + 0.2 * vol_ok + 0.2 * outlier_ok))


class DataIngestionEngine:
    API_ENDPOINTS = {
        "testnet": "https://testnet.binancefuture.com",
        "live": "https://fapi.binance.com",
    }

    TIMEFRAME_MS = {
        "1m": 60000, "3m": 180000, "5m": 300000, "15m": 900000,
        "30m": 1800000, "1h": 3600000, "2h": 7200000, "4h": 14400000,
        "6h": 21600000, "8h": 28800000, "12h": 43200000, "1d": 86400000,
        "3d": 259200000, "1w": 604800000, "1M": 2592000000,
    }

    def __init__(self, config: DataConfig, validator: Optional[DataValidator] = None,
                 repair_engine: Optional[GapRepairEngine] = None, scorer: Optional[DataQualityScorer] = None,
                 api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.config = config
        self.validator = validator or DataValidator()
        self.repair_engine = repair_engine or GapRepairEngine()
        self.scorer = scorer or DataQualityScorer()
        self.api_key = api_key
        self.api_secret = api_secret
        self._data_dir = Path(config.data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        logger.info(f"🔄 DataIngestionEngine started: {self.config.symbol}/{self.config.timeframe} ({self.config.env})")

    async def fetch_historical_range(self, symbol: Optional[str] = None, timeframe: Optional[str] = None,
                                     start_date: str = "2024-01-01", end_date: Optional[str] = None,
                                     batch_size: int = 1000) -> pd.DataFrame:
        symbol = symbol or self.config.symbol
        timeframe = timeframe or self.config.timeframe
        end_date = end_date or time.strftime("%Y-%m-%d")

        start_ts = int(pd.to_datetime(start_date).timestamp() * 1000)
        end_ts = int(pd.to_datetime(end_date).timestamp() * 1000)
        interval_ms = self._get_interval_ms(timeframe)

        all_candles = []
        current_ts = start_ts

        logger.info(f"📥 Fetching {symbol} {timeframe} from {start_date} to {end_date}")

        while current_ts < end_ts:
            try:
                batch = await self._fetch_klines(symbol, timeframe, current_ts, limit=batch_size)
                if batch.empty:
                    break

                all_candles.append(batch)

                # ✅ FIX: Access the Timestamp INDEX, not the column
                # batch.index is a DatetimeIndex, so we use .max() on the index
                last_ts = batch.index.max()
                # Convert pandas Timestamp (nanoseconds) back to milliseconds
                current_ts = int(last_ts.value / 1e6) + interval_ms

                if len(all_candles) % 10 == 0:
                    logger.info(f"📊 Progress: {len(all_candles) * batch_size} candles fetched")

                # Rate limit sleep
                await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"❌ Error fetching batch at {current_ts}: {e}")
                break

        if not all_candles:
            logger.warning("⚠️ No data fetched")
            return pd.DataFrame()

        df = pd.concat(all_candles)
        # Remove duplicates (in case of overlap) and sort
        df = df[~df.index.duplicated(keep="first")].sort_index()

        # Validate & Score
        df = self.validator.validate_schema(df, CandleSchema())
        df.attrs["quality_score"] = self.scorer.compute_quality_score(df)

        logger.info(f"✅ Fetched {len(df)} candles for {symbol} {timeframe}")
        return df

    async def _fetch_klines(self, symbol: str, timeframe: str, start_time: Optional[int] = None,
                            end_time: Optional[int] = None, limit: int = 1000) -> pd.DataFrame:
        base_url = self.API_ENDPOINTS.get(self.config.env, self.API_ENDPOINTS["testnet"])
        url = f"{base_url}/fapi/v1/klines"

        params = {
            "symbol": symbol.upper(),
            "interval": timeframe,
            "limit": min(limit, 1500),
        }
        if start_time: params["startTime"] = start_time
        if end_time: params["endTime"] = end_time

        # Add signature if keys provided
        headers = {}
        if self.api_key and self.api_secret:
            timestamp = int(time.time() * 1000)
            params["timestamp"] = timestamp
            query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            signature = hmac.new(self.api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
            params["signature"] = signature
            headers = {"X-MBX-APIKEY": self.api_key}

        def _sync_request():
            try:
                # Use requests for Windows DNS stability
                resp = requests.get(url, params=params, headers=headers, timeout=30)
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                logger.error(f"❌ HTTP error: {e}")
                return []

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, _sync_request)

        if not data:        # ← Fixed: check if API returned empty/no data
            return pd.DataFrame()

        columns = [
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ]
        df = pd.DataFrame(data, columns=columns)

        # Convert timestamp to datetime and set as index
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])

        return df

    def _get_interval_ms(self, timeframe: str) -> int:
        return self.TIMEFRAME_MS.get(timeframe, 900000)

    # ... (rest of the methods like save_to_parquet, fetch_batch etc remain the same)
    # ... If you have them, keep them. If not, the class above is the core logic.