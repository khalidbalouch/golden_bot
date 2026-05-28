import pytest
import asyncio
from core.rate_limiter import BinanceRateLimiter
from core.ws_manager import BinanceWSManager
from core.execution.router import SmartOrderRouter
from core.security import AuditLogger

@pytest.fixture
def router():
    rl = BinanceRateLimiter(ip_limit_per_min=100, order_limit_per_10s=10)
    ws = BinanceWSManager()
    return SmartOrderRouter(rl, ws)

@pytest.mark.asyncio
async def test_submit_order_respects_limits(router):
    tasks = [router.submit_order("BTCUSDT", "BUY", 0.01, 50000) for _ in range(12)]
    results = await asyncio.gather(*tasks)
    assert all(r.get("status") == "SUBMITTED" for r in results)

def test_ws_cache():
    handler = lambda d: d
    m = BinanceWSManager()
    m.register_handler("executionReport", handler)
    assert "executionReport" in m._handlers
