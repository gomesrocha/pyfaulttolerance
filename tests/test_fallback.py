from pyfaulttolerance.fallback import fallback
import asyncio

# Função de fallback que será usada quando a principal falhar
async def fallback_func():
    return "fallback value"

# Função principal que sempre falha
@fallback(fallback_func)
async def always_fail():
    raise Exception("Simulated error")

def test_fallback():
    result = asyncio.run(always_fail())
    assert result == "fallback value"
