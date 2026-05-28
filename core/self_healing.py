from __future__ import annotations
import asyncio
import logging
import psutil
import time
from typing import Dict, Optional, Callable

logger = logging.getLogger("golden_bot.self_healing")

class HealthMonitor:
    """AI-inspired anomaly detection & auto-recovery."""
    def __init__(self, threshold_cpu: float = 90.0, threshold_mem: float = 85.0):
        self.cpu_thresh = threshold_cpu
        self.mem_thresh = threshold_mem
        self._restart_callbacks: Dict[str, Callable] = {}

    def register_callback(self, component_id: str, callback: Callable) -> None:
        self._restart_callbacks[component_id] = callback

    async def monitor_loop(self) -> None:
        """Continuously checks system health and triggers recovery."""
        logger.info("🩺 Health Monitor started...")
        while True:
            try:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().percent

                if cpu > self.cpu_thresh:
                    logger.warning(f"⚠️ High CPU usage: {cpu}%. Triggering GC & cleanup...")
                    await self._emergency_cleanup()

                if mem > self.mem_thresh:
                    logger.critical(f"🚨 High Memory usage: {mem}%. Restarting components...")
                    await self._restart_heavy_components()

                await asyncio.sleep(60) # Check every minute
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)

    async def _emergency_cleanup(self) -> None:
        import gc
        gc.collect()

    async def _restart_heavy_components(self) -> None:
        for cid, cb in self._restart_callbacks.items():
            try:
                logger.info(f"🔄 Restarting component: {cid}")
                await cb()
            except Exception as e:
                logger.error(f"Failed to restart {cid}: {e}")
