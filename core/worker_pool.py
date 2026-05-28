from __future__ import annotations
import asyncio
import logging
import signal
import time
from typing import Dict, Callable, Any, Optional
from core.task_queue import RedisTaskQueue, Task
from utils.graceful_shutdown import register_shutdown_hook

logger = logging.getLogger("golden_bot.orchestration.worker_pool")

class WorkerPool:
    """Distributed worker pool with dynamic concurrency & graceful shutdown."""
    def __init__(self, queue: RedisTaskQueue, max_workers: int = 4, worker_id: Optional[str] = None):
        self.queue = queue
        self.max_workers = max_workers
        self.worker_id = worker_id or f"worker_{int(time.time())}_{os.getpid()}"
        self._handlers: Dict[str, Callable] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._shutdown = False

    def register_handler(self, task_type: str, handler: Callable[[Dict], Any]) -> None:
        self._handlers[task_type] = handler
        logger.info(f"🔧 Registered handler for task type: {task_type}")

    async def start(self) -> None:
        register_shutdown_hook(self._on_shutdown)
        self._shutdown = False
        logger.info(f"🚀 Worker pool started: {self.worker_id} (max_workers={self.max_workers})")

        tasks = [asyncio.create_task(self._worker_loop(i)) for i in range(self.max_workers)]
        await asyncio.gather(*tasks)

    async def _worker_loop(self, worker_idx: int) -> None:
        worker_name = f"{self.worker_id}_{worker_idx}"
        while not self._shutdown:
            try:
                task = await self.queue.dequeue(worker_name, timeout=1.0)
                if not task: continue

                handler = self._handlers.get(task.task_type)
                if not handler:
                    await self.queue.fail(task.task_id, f"No handler for {task.task_type}", retry=False)
                    continue

                result = await handler(task.payload)
                await self.queue.complete(task.task_id, result)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"⚠️ Worker {worker_name} error: {e}")
                await asyncio.sleep(0.5)

    async def _on_shutdown(self) -> None:
        logger.info(f"🛑 Graceful shutdown initiated for {self.worker_id}")
        self._shutdown = True
        for t in self._tasks.values():
            t.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
