import asyncio
import functools
import logging
from pyfaulttolerance.exceptions import TimeoutError

logger = logging.getLogger(__name__)

def timeout_async(seconds=5):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Timeout: function '{func.__name__}' exceeded {seconds}s")
                raise TimeoutError(func.__name__)
        return wrapper
    return decorator
