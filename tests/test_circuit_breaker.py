import pytest
import asyncio
import time
from pyfaulttolerance.circuit_breaker import CircuitBreaker
from pyfaulttolerance.exceptions import CircuitBreakerOpenError

# --- Helper ---
class MockService:
    def __init__(self):
        self._should_fail = False
        self.call_count = 0

    def set_should_fail(self, should_fail):
        self._should_fail = should_fail

    async def async_call(self):
        self.call_count += 1
        await asyncio.sleep(0.001) # Simulate a brief async operation
        if self._should_fail:
            raise ValueError("Simulated failure")
        return "success"

    def sync_call(self):
        self.call_count += 1
        # time.sleep(0.001) # For sync, direct execution
        if self._should_fail:
            raise ValueError("Simulated failure")
        return "success"

# --- Existing Test Modified ---
def test_async_closed_to_open_transition_and_error_message():
    mock_service = MockService()
    # Use a local CB instance for test isolation
    cb_test = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1) # Short recovery for testing

    # Decorate the method of the mock_service instance for this test
    protected_async_call = cb_test(mock_service.async_call)

    mock_service.set_should_fail(True)
    # First failure
    with pytest.raises(ValueError, match="Simulated failure"):
        asyncio.run(protected_async_call())
    assert cb_test.current_state == "CLOSED", "CB should still be CLOSED after 1st failure"

    # Second failure (reaches threshold)
    with pytest.raises(ValueError, match="Simulated failure"):
        asyncio.run(protected_async_call())
    assert cb_test.current_state == "OPEN", "CB should be OPEN after 2nd failure"
    
    # Third call - should raise CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError, match=r"\[CircuitBreakerOpen\] Open circuit for function 'async_call'\."):
        asyncio.run(protected_async_call())
    assert mock_service.call_count == 2, "Original function should not be called when CB is OPEN"

# --- New Async Tests ---

def test_async_open_to_half_open_and_half_open_to_closed():
    mock_service = MockService()
    cb_test = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05) # Quick recovery
    protected_async_call = cb_test(mock_service.async_call)

    # 1. CLOSED -> OPEN
    mock_service.set_should_fail(True)
    with pytest.raises(ValueError, match="Simulated failure"):
        asyncio.run(protected_async_call())
    assert cb_test.current_state == "OPEN"

    # 2. OPEN -> HALF_OPEN
    time.sleep(0.06) # Wait for recovery_timeout
    # At this point, the next call should put it into HALF_OPEN
    
    mock_service.set_should_fail(False) # Configure next call to succeed
    # This call is in HALF_OPEN state
    result = asyncio.run(protected_async_call())
    assert result == "success"
    assert cb_test.current_state == "CLOSED", "CB should be CLOSED after success in HALF_OPEN"
    assert cb_test.failure_count == 0, "Failure count should reset after closing from HALF_OPEN"
    assert mock_service.call_count == 2 # Original function was called twice

def test_async_half_open_to_open():
    mock_service = MockService()
    cb_test = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
    protected_async_call = cb_test(mock_service.async_call)

    # 1. CLOSED -> OPEN
    mock_service.set_should_fail(True)
    with pytest.raises(ValueError):
        asyncio.run(protected_async_call())
    assert cb_test.current_state == "OPEN"

    # 2. OPEN -> HALF_OPEN (implicitly by waiting)
    time.sleep(0.06) 

    # 3. HALF_OPEN -> OPEN (failure in HALF_OPEN)
    # mock_service.set_should_fail(True) # Already true
    with pytest.raises(ValueError, match="Simulated failure"): # Call in HALF_OPEN fails
        asyncio.run(protected_async_call())
    assert cb_test.current_state == "OPEN", "CB should be OPEN after failure in HALF_OPEN"
    assert mock_service.call_count == 2 # Original function called twice

    # Verify it's truly OPEN again
    with pytest.raises(CircuitBreakerOpenError):
        asyncio.run(protected_async_call())
    assert mock_service.call_count == 2 # Not called again

def test_async_successful_calls_in_closed_state_resets_failures():
    mock_service = MockService()
    cb_test = CircuitBreaker(failure_threshold=3, recovery_timeout=0.1)
    protected_async_call = cb_test(mock_service.async_call)

    # Induce some failures but not enough to open
    mock_service.set_should_fail(True)
    with pytest.raises(ValueError):
        asyncio.run(protected_async_call())
    with pytest.raises(ValueError):
        asyncio.run(protected_async_call())
    assert cb_test.failure_count == 2
    assert cb_test.current_state == "CLOSED"

    # A successful call should reset failure count
    mock_service.set_should_fail(False)
    result = asyncio.run(protected_async_call())
    assert result == "success"
    assert cb_test.failure_count == 0, "Failure count should reset after a successful call in CLOSED state"
    assert cb_test.current_state == "CLOSED"
    assert mock_service.call_count == 3

def test_async_call_succeeds_when_closed_no_prior_failures():
    mock_service = MockService()
    cb_test = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    protected_async_call = cb_test(mock_service.async_call)

    mock_service.set_should_fail(False)
    result = asyncio.run(protected_async_call())
    assert result == "success"
    assert cb_test.current_state == "CLOSED"
    assert cb_test.failure_count == 0
    assert mock_service.call_count == 1

# --- Sync Function Wrapping Tests ---

def test_sync_closed_to_open():
    mock_service = MockService()
    cb_test = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
    protected_sync_call = cb_test(mock_service.sync_call)

    mock_service.set_should_fail(True)
    with pytest.raises(ValueError, match="Simulated failure"):
        protected_sync_call()
    assert cb_test.current_state == "OPEN"
    
    with pytest.raises(CircuitBreakerOpenError, match=r"\[CircuitBreakerOpen\] Open circuit for function 'sync_call'\."):
        protected_sync_call()
    assert mock_service.call_count == 1

def test_sync_open_to_half_open_to_closed():
    mock_service = MockService()
    cb_test = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
    protected_sync_call = cb_test(mock_service.sync_call)

    mock_service.set_should_fail(True)
    with pytest.raises(ValueError): # CLOSED -> OPEN
        protected_sync_call()
    
    time.sleep(0.06) # Wait for recovery: OPEN -> HALF_OPEN

    mock_service.set_should_fail(False) # Next call in HALF_OPEN will succeed
    result = protected_sync_call()
    assert result == "success"
    assert cb_test.current_state == "CLOSED", "CB should be CLOSED after success in HALF_OPEN"
    assert cb_test.failure_count == 0
    assert mock_service.call_count == 2

def test_sync_half_open_to_open():
    mock_service = MockService()
    cb_test = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
    protected_sync_call = cb_test(mock_service.sync_call)

    mock_service.set_should_fail(True)
    with pytest.raises(ValueError): # CLOSED -> OPEN
        protected_sync_call()
    
    time.sleep(0.06) # Wait for recovery: OPEN -> HALF_OPEN

    # mock_service.set_should_fail(True) # Still true
    with pytest.raises(ValueError, match="Simulated failure"): # Call in HALF_OPEN fails
        protected_sync_call()
    assert cb_test.current_state == "OPEN", "CB should be OPEN after failure in HALF_OPEN"
    assert mock_service.call_count == 2

    with pytest.raises(CircuitBreakerOpenError): # Verify it's truly OPEN
        protected_sync_call()
    assert mock_service.call_count == 2

def test_sync_successful_call_resets_failures():
    mock_service = MockService()
    cb_test = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
    protected_sync_call = cb_test(mock_service.sync_call)

    mock_service.set_should_fail(True)
    with pytest.raises(ValueError): # 1st failure
        protected_sync_call()
    assert cb_test.failure_count == 1
    
    mock_service.set_should_fail(False) # Successful call
    result = protected_sync_call()
    assert result == "success"
    assert cb_test.failure_count == 0, "Failure count should reset"
    assert cb_test.current_state == "CLOSED"
    assert mock_service.call_count == 2

# Test that function name is correctly captured for unnamed (lambda) functions
def test_lambda_function_name_in_error():
    cb_lambda_test = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
    
    # Use a lambda that will be decorated
    protected_lambda = cb_lambda_test(lambda: (_ for _ in ()).throw(ValueError("Lambda error"))) # Fails
    
    with pytest.raises(ValueError, match="Lambda error"):
        protected_lambda()
    
    assert cb_lambda_test.current_state == "OPEN"
    with pytest.raises(CircuitBreakerOpenError, match=r"\[CircuitBreakerOpen\] Open circuit for function '<lambda>'\."):
        protected_lambda()

# Test that CircuitBreaker can be used as a context manager (if supported by design)
# This is a common pattern, but not explicitly asked for. Adding a placeholder if it makes sense.
# For now, focusing on decorator usage as shown in the existing test.

# Final check on requirements:
# 1. State Transitions: Covered for async and sync.
#    - CLOSED -> OPEN
#    - OPEN -> HALF_OPEN
#    - HALF_OPEN -> CLOSED
#    - HALF_OPEN -> OPEN
# 2. Error Raising: CircuitBreakerOpenError tested with correct message format for async, sync, and lambda.
# 3. Successful Calls:
#    - Calls succeed when CLOSED: Covered.
#    - Failure count resets: Covered for both async and sync.
# 4. Synchronous Function Wrapping: Covered.

# Removed the global `cb` instance and `falha_controlada` function from original example.
# Tests now use local CB instances and a MockService for better isolation and control.
# Recovery timeouts are short to speed up tests.
# `time.sleep` is used to wait for recovery periods.
# Function names in error messages are verified (e.g. 'async_call', 'sync_call', '<lambda>').
# Call counts on the mock service are checked to ensure the original function is not called when CB is OPEN.
# Checked current_state and failure_count attributes of the CircuitBreaker instance.
# The MockService helper class simplifies setting up fail/succeed behavior for wrapped functions.
# All tests should be independent.
