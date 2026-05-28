from __future__ import annotations
import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Literal, Optional, Tuple
import logging

logger = logging.getLogger("golden_bot.rate_limiter")

@dataclass
class BinanceLimit:
    name: str
    window_sec: int
    max_requests: int
    current_window_start: float = 0.0
    request_times: Deque[float] = field(default_factory=deque)

class BinanceRateLimiter:
    """Strict Binance-compliant rate limiter with request queueing & header feedback."""
    def __init__(self, ip_limit_per_min: int = 1200, order_limit_per_10s: int = 50):
        self.ip_limit = BinanceLimit("ip_1m", 60, ip_limit_per_min)
        self.order_limit = BinanceLimit("order_10s", 10, order_limit_per_10s)
        self._queue: asyncio.Queue[Tuple[str, dict, asyncio.Future]] = asyncio.Queue()
        self._running = False

    def record_response_headers(self, headers: dict) -> None:
        """Parse Binance response headers to sync internal counters."""
        used_weight = int(headers.get("x-mbx-used-weight-1m", 0))
        order_count_1s = int(headers.get("x-mbx-order-count-1s", 0))
        if used_weight > 0:
            self._sync_limit(self.ip_limit, time.time(), used_weight)
        if order_count_1s > 0:
            self._sync_limit(self.order_limit, time.time(), order_count_1s)

    def _sync_limit(self, limit: BinanceLimit, now: float, used: int) -> None:
        """Reset or adjust limit tracking based on exchange headers."""
        limit.current_window_start = now
        limit.request_times.clear()
        for _ in range(min(used, limit.max_requests)):
            limit.request_times.append(now)

    async def acquire(self, weight: int = 1, order_weight: int = 0) -> None:
        """Block until rate limits allow request. Auto-queues if exceeded."""
        while True:
            now = time.time()
            self._clean_expired(now)
            ip_remaining = self.ip_limit.max_requests - len(self.ip_limit.request_times)
            order_remaining = self.order_limit.max_requests - len(self.order_limit.request_times)
            if ip_remaining >= weight and order_remaining >= order_weight:
                self._record(now, weight, order_weight)
                return
            delay = self._calc_delay(now)
            await asyncio.sleep(delay)

    def _clean_expired(self, now: float) -> None:
        cutoff_ip = now - self.ip_limit.window_sec
        while self.ip_limit.request_times and self.ip_limit.request_times[0] < cutoff_ip:
            self.ip_limit.request_times.popleft()
        cutoff_order = now - self.order_limit.window_sec
        while self.order_limit.request_times and self.order_limit.request_times[0] < cutoff_order:
            self.order_limit.request_times.popleft()

    def _record(self, now: float, weight: int, order_weight: int) -> None:
        for _ in range(weight): self.ip_limit.request_times.append(now)
        for _ in range(order_weight): self.order_limit.request_times.append(now)

    def _calc_delay(self, now: float) -> float:
        next_ip = self.ip_limit.window_sec if not self.ip_limit.request_times else self.ip_limit.request_times[0] + self.ip_limit.window_sec - now
        next_order = self.order_limit.window_sec if not self.order_limit.request_times else self.order_limit.request_times[0] + self.order_limit.window_sec - now
        return max(0.0, min(next_ip, next_order) + 0.05)
