import asyncio
from app.retry_async import retry_async
from app.timeout_async import timeout_async
from app.fallback import fallback
from app.bulkhead import bulkhead
from app.circuit_breaker import CircuitBreaker
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

# Fallback de exemplo
async def fallback_example():
    print("[fallback] Executando fallback...")
    return {"status": "fallback activated"}

# 1. Retry: tenta novamente até 3 vezes
@retry_async(max_attempts=3, delay=1)
async def usar_retry():
    print("[retry] Tentando operação...")
    raise Exception("Erro temporário")

# 2. Timeout: cancela após 2 segundos
@timeout_async(seconds=2)
async def usar_timeout():
    print("[timeout] Iniciando tarefa longa...")
    await asyncio.sleep(5)
    return {"status": "finalizado"}

# 3. Bulkhead: limita concorrência a 1 execução
@bulkhead(max_concurrent_calls=1)
async def usar_bulkhead(i):
    print(f"[bulkhead] Execução {i}")
    await asyncio.sleep(2)
    return {"status": f"bulkhead {i} finalizado"}

# 4. Fallback: usa função alternativa em caso de erro
@fallback(fallback_example)
async def usar_fallback():
    print("[fallback] Forçando erro para acionar fallback...")
    raise Exception("Erro planejado")

# 5. Circuit Breaker: abre após 2 falhas consecutivas
cb = CircuitBreaker(failure_threshold=2, recovery_timeout=5)

@cb
async def usar_circuit_breaker():
    print("[circuit breaker] Chamando serviço instável...")
    raise Exception("Erro no serviço instável")

# Função principal de execução dos testes
async def main():
    print("➡️ Teste 1: Retry")
    try:
        await usar_retry()
    except Exception as e:
        print("Resultado final (retry):", e)

    print("\n➡️ Teste 2: Timeout")
    try:
        await usar_timeout()
    except Exception as e:
        print("Resultado final (timeout):", e)

    print("\n➡️ Teste 3: Bulkhead (executando 2 concorrentes)")
    try:
        await asyncio.gather(usar_bulkhead(1), usar_bulkhead(2))
    except Exception as e:
        print("Erro no bulkhead:", e)

    print("\n➡️ Teste 4: Fallback")
    result = await usar_fallback()
    print("Resultado final (fallback):", result)

    print("\n➡️ Teste 5: Circuit Breaker")
    for i in range(4):
        try:
            await usar_circuit_breaker()
        except Exception as e:
            print(f"  Tentativa {i+1}: {e}")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
