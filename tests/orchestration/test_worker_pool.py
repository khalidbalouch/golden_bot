import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.worker_pool import WorkerPool
from core.task_queue import RedisTaskQueue, Task

@pytest.mark.asyncio
async def test_worker_routes_to_handler():
    q = AsyncMock()
    q.dequeue = AsyncMock(side_effect=[
        Task(task_id="t1", task_type="predict", payload={"v": 1}),
        None
    ])
    q.complete = AsyncMock()

    pool = WorkerPool(q, max_workers=1)
    results = []
    pool.register_handler("predict", lambda p: results.append(p))

    await pool.start()
    assert len(results) == 1
    assert results[0] == {"v": 1}
