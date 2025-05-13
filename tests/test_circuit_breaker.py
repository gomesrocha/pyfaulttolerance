import pytest
from app.circuit_breaker import CircuitBreaker
import asyncio

# Instância do circuit breaker com 2 falhas antes de abrir o circuito
cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

@cb
async def falha_controlada():
    raise Exception("Erro controlado")

def test_circuit_breaker_abre_apos_falhas():
    # Primeira e segunda chamadas causam falha → abre circuito
    for _ in range(2):
        with pytest.raises(Exception, match="Erro controlado"):
            asyncio.run(falha_controlada())

    # Terceira chamada deve falhar imediatamente com circuito aberto
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        asyncio.run(falha_controlada())
