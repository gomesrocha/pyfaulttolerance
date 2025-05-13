import asyncio
import functools
from app.exceptions import BulkheadRejectionError
import logging
logger = logging.getLogger(__name__)


def bulkhead(max_concurrent_calls=5):
    semaphore = asyncio.Semaphore(max_concurrent_calls)

    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):

                acquired = semaphore.locked() or not semaphore._value
                if acquired:
                    logger.warning(f"[Bulkhead] Concurrent execution rejected in '{func.__name__}'")
                    raise BulkheadRejectionError(func.__name__)
                async with semaphore:
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            raise RuntimeError("Bulkhead only supports async functions.")
    return decorator
