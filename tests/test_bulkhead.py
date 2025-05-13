import pytest
import asyncio
from pyfaulttolerance.bulkhead import bulkhead
from pyfaulttolerance.exceptions import BulkheadRejectionError

@bulkhead(max_concurrent_calls=1)
async def tarefa_lenta(index):
    await asyncio.sleep(1)
    return f"executado {index}"

def test_bulkhead_concorrente():
    async def executar():
        await asyncio.gather(tarefa_lenta(1), tarefa_lenta(2))

    with pytest.raises(BulkheadRejectionError, match="competition limits"):
        asyncio.run(executar())
