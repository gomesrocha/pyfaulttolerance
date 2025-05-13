import asyncio
import functools

class TimeoutException(Exception): pass

def timeout_async(seconds=5):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutException("Function timed out")
        return wrapper
    return decorator
