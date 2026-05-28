from __future__ import annotations
import asyncio
import logging
import time
from enum import Enum
from typing import List, Optional
import ntplib

logging.basicConfig(level=logging.INFO, format='{"ts":"%(asctime)s","lvl":"%(levelname)s","mod":"%(name)s","msg":"%(message)s"}')
logger = logging.getLogger("golden_bot.time_sync")

class TimeSyncStatus(Enum):
    SYNCED = "SYNCED"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNREACHABLE = "UNREACHABLE"

class TimeSyncValidator:
    def __init__(self, ntp_servers: List[str] = ["pool.ntp.org"], max_drift_ms: int = 100):
        self.servers = ntp_servers
        self.max_drift = max_drift_ms
        self._last_status = TimeSyncStatus.SYNCED
        self._drift_ms = 0.0

    async def check_time_sync(self) -> TimeSyncStatus:
        try:
            client = ntplib.NTPClient()
            resp = client.request(self.servers[0], version=3, timeout=2.0)
            drift = (resp.offset * 1000)
            self._drift_ms = drift
            if abs(drift) < 50: status = TimeSyncStatus.SYNCED
            elif abs(drift) < 100: status = TimeSyncStatus.WARNING
            else: status = TimeSyncStatus.CRITICAL
            self._last_status = status
        except Exception as e:
            logger.error(f"NTP sync failed: {e}")
            self._last_status = TimeSyncStatus.UNREACHABLE
        return self._last_status

    def get_drift_ms(self) -> float: return self._drift_ms
    def should_pause_ingestion(self) -> bool: return self._last_status in (TimeSyncStatus.CRITICAL, TimeSyncStatus.UNREACHABLE)
