from __future__ import annotations
import logging
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from utils.data_validator import GapInfo

logger = logging.getLogger("golden_bot.gap_repair")

class RepairStrategy(ABC):
    @abstractmethod
    def can_handle(self, gap: GapInfo) -> bool: pass
    @abstractmethod
    def execute(self, gap: GapInfo, context: Optional[dict] = None) -> pd.DataFrame: pass

class LinearInterpolationStrategy(RepairStrategy):
    def can_handle(self, gap: GapInfo) -> bool: return 1 <= gap.size <= 5
    def execute(self, gap: GapInfo, context: Optional[dict] = None) -> pd.DataFrame:
        idx = range(gap.start_ts + gap.expected_interval_ms, gap.end_ts, gap.expected_interval_ms)
        return pd.DataFrame(index=idx).reset_index().rename(columns={"index":"timestamp"}).assign(open=np.nan, high=np.nan, low=np.nan, close=np.nan, volume=0.0).interpolate()

class ForwardFillStrategy(RepairStrategy):
    def can_handle(self, gap: GapInfo) -> bool: return gap.size == 1
    def execute(self, gap: GapInfo, context: Optional[dict] = None) -> pd.DataFrame:
        base = context.get("last_candle")
        if base is None: return pd.DataFrame()
        row = base.copy()
        row["timestamp"] = gap.start_ts + gap.expected_interval_ms
        return pd.DataFrame([row])

class BackupFetchStrategy(RepairStrategy):
    def can_handle(self, gap: GapInfo) -> bool: return gap.size <= 60
    def execute(self, gap: GapInfo, context: Optional[dict] = None) -> pd.DataFrame:
        logger.info(f"🔄 Fetching backup data for gap {gap.start_ts}->{gap.end_ts}")
        return pd.DataFrame()

class MarkMissingStrategy(RepairStrategy):
    def can_handle(self, gap: GapInfo) -> bool: return gap.size > 60
    def execute(self, gap: GapInfo, context: Optional[dict] = None) -> pd.DataFrame:
        logger.warning(f"⚠️ Large gap marked as MISSING: {gap.size} candles")
        return pd.DataFrame()

class GapRepairEngine:
    def __init__(self):
        self.strategies: List[RepairStrategy] = [LinearInterpolationStrategy(), ForwardFillStrategy(), BackupFetchStrategy(), MarkMissingStrategy()]

    async def repair_gap(self, gap: GapInfo, symbol: str, context: Optional[dict] = None) -> pd.DataFrame:
        for strat in self.strategies:
            if strat.can_handle(gap):
                return strat.execute(gap, context)
        return pd.DataFrame()
