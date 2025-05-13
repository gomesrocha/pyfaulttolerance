import pytest
from pyfaulttolerance.timeout_async import timeout_async
from pyfaulttolerance.exceptions import TimeoutError
import asyncio

@timeout_async(seconds=1)
async def slow_function():
    await asyncio.sleep(2)

def test_timeout_async():
    with pytest.raises(TimeoutError):
        asyncio.run(slow_function())
