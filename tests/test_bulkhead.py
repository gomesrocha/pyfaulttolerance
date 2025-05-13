import pytest
from app.bulkhead import bulkhead
import asyncio

@bulkhead(max_concurrent_calls=1)
async def tarefa_lenta(index):
    await asyncio.sleep(1)
    return f"executado {index}"

def test_bulkhead_concorrente():
    async def executar():
        # A segunda chamada simultânea deve causar erro
        await asyncio.gather(tarefa_lenta(1), tarefa_lenta(2))

    with pytest.raises(RuntimeError, match="another call is already in progress"):
        asyncio.run(executar())
