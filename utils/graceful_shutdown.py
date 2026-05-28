from __future__ import annotations
import asyncio
import logging
import signal
import os
import json
from pathlib import Path
from typing import Callable, Awaitable, List

logger = logging.getLogger("golden_bot.orchestration.shutdown")

_shutdown_handlers: List[Callable[[], Awaitable[None]]] = []
_state_file = Path("data/last_state.json")

def register_shutdown_hook(handler: Callable[[], Awaitable[None]]) -> None:
    _shutdown_handlers.append(handler)

async def _execute_shutdown() -> None:
    logger.info("🛑 Executing graceful shutdown sequence...")
    for handler in _shutdown_handlers:
        try:
            await handler()
        except Exception as e:
            logger.error(f"Shutdown handler failed: {e}")
    logger.info("✅ Graceful shutdown complete. Exiting.")
    os._exit(0)

def setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(_execute_shutdown()))
    logger.info("📡 Signal handlers registered (SIGTERM, SIGINT)")

async def persist_state(state: dict) -> None:
    _state_file.parent.mkdir(parents=True, exist_ok=True)
    _state_file.write_text(json.dumps(state, indent=2))
    logger.debug(f"💾 State persisted to {_state_file}")

async def load_state() -> dict:
    if _state_file.exists():
        return json.loads(_state_file.read_text())
    return {}
