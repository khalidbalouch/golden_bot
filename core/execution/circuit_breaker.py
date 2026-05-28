from __future__ import annotations
import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger("golden_bot.exec.circuit_breaker")

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0, half_open_max: int = 2):
        self._threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max = half_open_max
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time = 0.0
        self._half_open_tries = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_tries = 0
            else:
                raise RuntimeError("Circuit breaker OPEN")

        if self._state == CircuitState.HALF_OPEN and self._half_open_tries >= self._half_open_max:
            self._state = CircuitState.OPEN
            raise RuntimeError("Circuit breaker OPEN (half-open limit)")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self) -> None:
        self._failures = 0
        self._half_open_tries = 0
        if self._state == CircuitState.HALF_OPEN: self._state = CircuitState.CLOSED

    def _on_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.time()
        self._half_open_tries += 1
        if self._failures >= self._threshold: self._state = CircuitState.OPEN

    @property
    def state(self) -> CircuitState: return self._state
