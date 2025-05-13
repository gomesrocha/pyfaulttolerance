import asyncio
import functools

def bulkhead(max_concurrent_calls=5):
    semaphore = asyncio.Semaphore(max_concurrent_calls)

    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Tenta adquirir sem esperar — se falhar, lança erro
                acquired = semaphore.locked() or not semaphore._value
                if acquired:
                    raise RuntimeError("another call is already in progress")

                async with semaphore:
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            raise RuntimeError("bulkhead only supports async functions.")
    return decorator
