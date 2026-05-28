import pytest
import time
from core.rate_limiter import BinanceRateLimiter

@pytest.mark.asyncio
async def test_acquire_delays():
    rl = BinanceRateLimiter(ip_limit_per_min=5, order_limit_per_10s=2)
    start = time.time()
    await rl.acquire()
    await rl.acquire(order_weight=1)
    assert time.time() - start < 2.0
