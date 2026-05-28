import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.task_queue import RedisTaskQueue, Task

@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.zpopmin = AsyncMock(return_value=[("{}", 0)])
    r.hset = AsyncMock()
    r.hdel = AsyncMock()
    r.expire = AsyncMock()
    return r

@pytest.mark.asyncio
async def test_enqueue_and_dequeue(mock_redis):
    with patch("redis.asyncio.from_url", return_value=mock_redis):
        q = RedisTaskQueue()
        t = Task(task_id="test_1", task_type="prediction", payload={"x": 1})
        await q.enqueue(t)

        popped = await q.dequeue("worker_1")
        assert popped is not None
        mock_redis.hset.assert_called_once()
