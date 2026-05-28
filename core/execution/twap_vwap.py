from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, Optional, List
import numpy as np

logger = logging.getLogger("golden_bot.exec.twap_vwap")

@dataclass
class VolumeProfile:
    timestamps: List[int]
    volumes: List[float]

class TWAPExecutor:
    def __init__(self, total_qty: float, duration_min: int, slices: int = 5):
        self.total_qty = total_qty
        self.duration = duration_min * 60
        self.slices = slices
        self.slice_qty = total_qty / slices

    async def generate_slices(self) -> AsyncGenerator[float, None]:
        interval = self.duration / self.slices
        for _ in range(self.slices):
            yield self.slice_qty
            await asyncio.sleep(interval)

class VWAPExecutor:
    def __init__(self, total_qty: float, profile: VolumeProfile, participation_rate: float = 0.05):
        self.total_qty = total_qty
        self.profile = profile
        self.rate = participation_rate
        self.remaining = total_qty

    async def generate_slices(self) -> AsyncGenerator[float, None]:
        total_vol = sum(self.profile.volumes)
        if total_vol == 0:
            yield self.total_qty
            return
        weights = [v / total_vol for v in self.profile.volumes]
        for w in weights:
            slice_qty = min(self.total_qty * w * self.rate, self.remaining)
            if slice_qty <= 0: continue
            self.remaining -= slice_qty
            yield slice_qty
