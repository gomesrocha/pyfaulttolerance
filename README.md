# PyFaultTolerance

[![codecov](https://codecov.io/gh/gomesrocha/pyfaulttolerance/graph/badge.svg?token=2BTCB8BN3V)](https://codecov.io/gh/gomesrocha/pyfaulttolerance)


> Um microframework Python para **tolerância a falhas assíncrona**, inspirado no SmallRye Fault Tolerance.  
> Ideal para sistemas resilientes que utilizam `asyncio` ou `FastAPI`.

---

## ✨ Funcionalidades

- ✅ `@timeout_async`: interrompe execução que exceder o tempo limite
- 🔁 `@retry_async`: reexecuta em caso de falha, com controle de tentativas
- 🧱 `@bulkhead`: limita concorrência simultânea (isolamento de chamadas)
- 🔌 `@fallback`: define alternativa automática em caso de falha
- 🚧 `CircuitBreaker`: previne chamadas para funções que falharam repetidamente
- 📦 Exceções personalizadas com logs estruturados

---

## 📦 Instalação
Você pode instalar a biblioteca diretamente do PyPI:

```bash
pip install pyfaulttolerance
```

---
## 🚀 Uso

### Timeout

```
from pyfaulttolerance.timeout import timeout, TimeoutException

@timeout(seconds=2)
def funcao_lenta():
    # código que pode demorar
    pass

```

### Retry

```
from pyfaulttolerance.retry_async import retry_async

@retry_async(max_attempts=3, delay=1)
async def funcao_instavel():
    # código que pode falhar
    pass

```

### Fallback
```
from pyfaulttolerance.fallback import fallback

async def alternativa():
    return "valor alternativo"

@fallback(alternativa)
async def funcao_principal():
    # código que pode falhar
    pass

```

### Bulkhead
```
from pyfaulttolerance.bulkhead import bulkhead

@bulkhead(max_concurrent_calls=2)
async def tarefa():
    # código que deve ser limitado em concorrência
    pass

```

### Circuit Breaker
```
from pyfaulttolerance.circuit_breaker import CircuitBreaker

cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10)

@cb
async def funcao():
    # código que pode falhar
    pass

```

---
## 📄 Licença
Este projeto está licenciado sob a Licença MIT. Consulte o arquivo LICENSE para mais detalhes.

Para mais informações, visite o repositório oficial: https://github.com/gomesrocha/pyfaulttolerance

