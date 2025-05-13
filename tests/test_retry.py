import pytest
from app.retry_async import retry_async

# Função instável que sempre falha
@retry_async(max_attempts=3, delay=0)
async def unstable_function():
    unstable_function.calls += 1
    raise Exception("Falha")

unstable_function.calls = 0

def test_retry_async():
    import asyncio

    with pytest.raises(Exception, match="Falha"):
        asyncio.run(unstable_function())

    assert unstable_function.calls == 3
