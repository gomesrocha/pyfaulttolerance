import pytest
from app.retry_async import retry_async
from app.exceptions import RetryExceededError
import asyncio

@retry_async(max_attempts=3, delay=0)
async def unstable_function():
    unstable_function.calls += 1
    raise Exception("Failure")

unstable_function.calls = 0

def test_retry_async():
    with pytest.raises(RetryExceededError, match="Failed after 3"):
        asyncio.run(unstable_function())

    assert unstable_function.calls == 3
