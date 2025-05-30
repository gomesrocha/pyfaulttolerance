# app/circuit_breaker.py
import time
import functools
import asyncio
from enum import Enum
from pyfaulttolerance.exceptions import CircuitBreakerOpenError
import logging
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    @property
    def current_state(self):
        return self.state.value # Access the string value of the enum

    def _check_state(self):
        if self.state == CircuitState.OPEN:
            if (time.time() - self.last_failure_time) >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
        return self.state

    def _record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def _record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def __call__(self, func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                state = self._check_state()
                if state == CircuitState.OPEN:
                    logger.error(f"[CircuitBreaker] Open circuit in '{func.__name__}'")
                    raise CircuitBreakerOpenError(func.__name__)

                try:
                    result = await func(*args, **kwargs)
                    self._record_success()
                    return result
                except Exception:
                    self._record_failure()
                    raise

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                state = self._check_state()
                if state == CircuitState.OPEN:
                    logger.error(f"[CircuitBreaker] Open circuit in '{func.__name__}'")
                    raise CircuitBreakerOpenError(func.__name__)

                try:
                    result = func(*args, **kwargs)
                    self._record_success()
                    return result
                except Exception:
                    self._record_failure()
                    raise

            return sync_wrapper
