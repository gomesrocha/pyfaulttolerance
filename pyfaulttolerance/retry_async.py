import asyncio
import functools
import logging
from app.exceptions import RetryExceededError
from app.exceptions import CircuitBreakerOpenError


logger = logging.getLogger(__name__)

def retry_async(max_attempts=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"[Retry] Attempt {attempt} failed in function '{func.__name__}': {e}")
                    if attempt == max_attempts:
                        logger.error(f"[Retry] Final failure after {max_attempts} in '{func.__name__}'")
                        raise RetryExceededError(func.__name__, max_attempts)
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
