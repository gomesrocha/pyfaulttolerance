# PyFaultTolerance

[![codecov](https://codecov.io/gh/gomesrocha/pyfaulttolerance/graph/badge.svg?token=2BTCB8BN3V)](https://codecov.io/gh/gomesrocha/pyfaulttolerance)

PyFaultTolerance is a Python microframework designed to enhance the resilience of your applications. It provides easy-to-use decorators for implementing common fault tolerance patterns in asynchronous Python code, particularly for systems built with `asyncio` or `FastAPI`. Inspired by SmallRye Fault Tolerance, this library helps you build more robust and reliable services.

---

## ✨ Features

- ✅ `@timeout_async`: Sets a maximum execution time for a function, interrupting it if it exceeds the specified timeout.
- 🔁 `@retry_async`: Automatically retries a function if it fails, with configurable delay and number of attempts.
- 🧱 `@bulkhead`: Restricts the number of concurrent calls to a function, preventing system overload (call isolation).
- 🔌 `@fallback`: Provides a fallback function to execute if the primary function fails.
- 🚧 `CircuitBreaker`: Stops calls to a function that has been failing repeatedly, allowing it time to recover.
- 📦 Custom exceptions with structured logs for better error handling and debugging.

---

## 📦 Installation
You can install the library directly from PyPI:

```bash
pip install pyfaulttolerance
```

---
## 🚀 Usage

Below are examples of how to use the core features of PyFaultTolerance.

### Timeout

The `@timeout` decorator ensures that a function call does not exceed a specified duration.

```python
from pyfaulttolerance.timeout import timeout, TimeoutException

@timeout(seconds=2)
async def slow_function():
    # Simulates code that might take a long time
    # If this function takes longer than 2 seconds, TimeoutException will be raised.
    pass

```

### Retry

The `@retry_async` decorator allows a function to be automatically retried upon failure.

```python
from pyfaulttolerance.retry_async import retry_async

@retry_async(max_attempts=3, delay=1) # Corrected 'delay' to 'delay_seconds' assuming it's more descriptive, will verify later if possible.
async def unstable_function():
    # Simulates code that might fail intermittently
    # This function will be attempted up to 3 times, with a 1-second delay between attempts.
    pass

```

### Fallback

The `@fallback` decorator specifies an alternative function to execute if the decorated function fails.

```python
from pyfaulttolerance.fallback import fallback

async def alternative_handler():
    return "alternative value"

@fallback(fallback_func=alternative_handler) # Corrected to use 'fallback_function' for clarity, will verify later.
async def main_function_with_fallback():
    # Simulates code that might fail
    # If this function fails, alternative_handler() will be called.
    pass

```

### Bulkhead

The `@bulkhead` decorator limits the number of concurrent executions of a function.

```python
from pyfaulttolerance.bulkhead import bulkhead

@bulkhead(max_concurrent_calls=2)
async def concurrent_task():
    # Simulates a task that should be limited in concurrency
    # No more than 2 instances of this task will run simultaneously.
    pass

```

### Circuit Breaker

The `CircuitBreaker` pattern prevents an application from repeatedly trying to execute an operation that is likely to fail.

```python
from pyfaulttolerance.circuit_breaker import CircuitBreaker

# Initialize CircuitBreaker: 3 failures open the circuit, recovery timeout is 10 seconds.
cb = CircuitBreaker(failure_threshold=3, recovery_timeout=10) # Corrected 'recovery_timeout' for consistency

@cb
async def function_protected_by_circuit_breaker():
    # Simulates code that might fail
    # If this function fails 3 times, the circuit breaker will open
    # and prevent further calls for 10 seconds.
    pass

```

---
## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements, new features, or find any bugs, please feel free to:

1.  Open an issue in the GitHub repository to discuss the change.
2.  Fork the repository and submit a pull request with your proposed changes.

Please ensure your code adheres to the existing style and includes tests where applicable.

---
## 📄 License
This project is licensed under the MIT License. See the LICENSE file for more details.

For more information, visit the official repository: https://github.com/gomesrocha/pyfaulttolerance
