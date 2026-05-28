from __future__ import annotations
import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass, asdict
import redis.asyncio as aioredis

logger = logging.getLogger("golden_bot.orchestration.task_queue")

@dataclass
class Task:
    task_id: str
    task_type: Literal["feature_compute", "prediction", "order_execution", "retrain", "backtest"]
    payload: Dict[str, Any]
    priority: int = 0
    created_at: float = 0.0
    visibility_timeout: int = 300
    retry_count: int = 0

class RedisTaskQueue:
    """Async Redis-backed task queue with visibility timeout & retry logic."""
    def __init__(self, redis_url: str = "redis://localhost:6379/0", queue_name: str = "golden_bot_tasks"):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.queue_name = queue_name
        self.processing_key = f"{queue_name}:processing"
        self._running = False

    async def enqueue(self, task: Task) -> str:
        task.created_at = time.time()
        score = time.time() + task.priority
        await self.redis.zadd(self.queue_name, {json.dumps(asdict(task)): score})
        logger.debug(f"📥 Enqueued task {task.task_id} (type={task.task_type})")
        return task.task_id

    async def dequeue(self, worker_id: str, timeout: float = 5.0) -> Optional[Task]:
        """Pop highest priority task, move to processing set with visibility timeout."""
        result = await self.redis.zpopmin(self.queue_name, count=1)
        if not result:
            await asyncio.sleep(timeout)
            return None
        task_data, _ = result[0]
        task = Task(**json.loads(task_data))
        expire_at = time.time() + task.visibility_timeout
        await self.redis.hset(self.processing_key, task.task_id, task_data)
        await self.redis.expire(self.processing_key, task.visibility_timeout)
        return task

    async def complete(self, task_id: str, result: Any = None) -> None:
        await self.redis.hdel(self.processing_key, task_id)
        logger.debug(f"✅ Task {task_id} completed")

    async def fail(self, task_id: str, error: str, retry: bool = True) -> None:
        task_data = await self.redis.hget(self.processing_key, task_id)
        if not task_data: return
        task = Task(**json.loads(task_data))
        await self.redis.hdel(self.processing_key, task_id)

        if retry and task.retry_count < 3:
            task.retry_count += 1
            backoff = 2 ** task.retry_count
            task.created_at = time.time() + backoff
            await self.redis.zadd(self.queue_name, {json.dumps(asdict(task)): task.created_at})
            logger.warning(f"🔄 Retrying task {task_id} (attempt {task.retry_count}) in {backoff}s")
        else:
            logger.error(f"❌ Task {task_id} failed permanently: {error}")

    async def cleanup_expired(self) -> int:
        """Requeue tasks whose visibility timeout expired."""
        expired = []
        async for key, val in self.redis.hscan_iter(self.processing_key):
            task = Task(**json.loads(val))
            if time.time() > task.created_at + task.visibility_timeout:
                expired.append(key)
        for tid in expired:
            await self.fail(tid, "Visibility timeout expired", retry=True)
        return len(expired)

    async def close(self) -> None:
        await self.redis.aclose()
