import pytest
import asyncio
from pyfaulttolerance.circuit_breaker import CircuitBreaker
from pyfaulttolerance.exceptions import CircuitBreakerOpenError

cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

@cb
async def falha_controlada():
    raise Exception("Controlled error")

def test_circuit_breaker_abre_apos_falhas():
    for _ in range(2):
        with pytest.raises(Exception, match="Controlled error"):
            asyncio.run(falha_controlada())

    with pytest.raises(CircuitBreakerOpenError, match="Open circuit"):
        asyncio.run(falha_controlada())
