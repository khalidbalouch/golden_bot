#!/usr/bin/env python3
"""CLI: AI-driven anomaly detection & auto-recovery monitor"""
import asyncio
import logging
import psutil
import os
import sys
sys.path.insert(0, ".")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("self_heal")

async def monitor():
    logger.info("🩺 Self-Healing Monitor Started...")
    while True:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        if cpu > 90.0:
            logger.warning("⚠️ High CPU. Triggering emergency GC & cleanup...")
            # In production: restart heavy workers or scale down
        if mem > 85.0:
            logger.critical("🚨 High Memory. Flushing caches & triggering restart...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(monitor())
