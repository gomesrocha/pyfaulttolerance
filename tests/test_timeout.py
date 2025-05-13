import pytest
from app.timeout_async import timeout_async, TimeoutException
import asyncio

# Função que demora mais que o timeout permitido
@timeout_async(seconds=1)
async def slow_function():
    await asyncio.sleep(2)

def test_timeout_async():
    with pytest.raises(TimeoutException, match="Function timed out"):
        asyncio.run(slow_function())
