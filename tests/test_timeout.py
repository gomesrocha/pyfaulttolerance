import pytest
from pyfaulttolerance.timeout_async import timeout_async
from pyfaulttolerance.exceptions import TimeoutError as AsyncTimeoutError # Alias for clarity
import asyncio
import time

# Import for synchronous timeout tests
from pyfaulttolerance.timeout import timeout, TimeoutException # Specific for sync timeout

# --- Existing Async Tests ---
@timeout_async(seconds=0.05) # Reduced time for faster test execution
async def async_slow_function_for_test(): # Renamed to avoid potential future conflicts
    await asyncio.sleep(0.1) # Sleep longer than timeout

@timeout_async(seconds=0.1)
async def async_timely_function_for_test():
    await asyncio.sleep(0.05)
    return "async completed"

def test_existing_timeout_async_exceeded(): # Renamed for clarity
    with pytest.raises(AsyncTimeoutError): # This is pyfaulttolerance.exceptions.TimeoutError
        asyncio.run(async_slow_function_for_test())

def test_existing_timeout_async_not_exceeded():
    result = asyncio.run(async_timely_function_for_test())
    assert result == "async completed"

# --- New Synchronous Timeout Tests ---

# Helper synchronous functions
def sync_function_sleeps_for(duration):
    time.sleep(duration)
    return "completed"

# 1. A synchronous function that exceeds the timeout duration
def test_sync_timeout_exceeded():
    timeout_seconds = 0.05
    @timeout(seconds=timeout_seconds)
    def sync_slow_function():
        time.sleep(timeout_seconds + 0.05) # Sleep longer than timeout
        return "should not return"

    with pytest.raises(TimeoutException, match=f"Timeout expired after {timeout_seconds} seconds"):
        sync_slow_function()

# 2. A synchronous function that completes within the timeout duration
def test_sync_timeout_not_exceeded():
    @timeout(seconds=0.1)
    def sync_timely_function():
        return sync_function_sleeps_for(0.05) # Sleep less than timeout

    result = sync_timely_function()
    assert result == "completed"

# 3. Test with different timeout values
def test_sync_timeout_very_short_timeout_definitely_exceeded():
    timeout_seconds = 0.01
    @timeout(seconds=timeout_seconds) 
    def sync_very_slow_function():
        time.sleep(timeout_seconds + 0.04) # Sleep significantly longer
        return "should not return"

    with pytest.raises(TimeoutException, match=f"Timeout expired after {timeout_seconds} seconds"):
        sync_very_slow_function()

def test_sync_timeout_longer_timeout_allows_completion():
    @timeout(seconds=0.2) 
    def sync_function_with_longer_timeout():
        return sync_function_sleeps_for(0.1) # Completes well within

    result = sync_function_with_longer_timeout()
    assert result == "completed"

# Test that arguments and return values work correctly when not timing out
def test_sync_timeout_with_args_and_return_value_not_exceeded():
    @timeout(seconds=0.1)
    def sync_function_with_args(val1, val2):
        time.sleep(0.01) # Well within timeout
        return val1 + val2

    result = sync_function_with_args(5, 10)
    assert result == 15

# Test that the original function's docstring and name are preserved (assumes @functools.wraps)
def test_sync_timeout_preserves_metadata():
    @timeout(seconds=0.01) # Timeout value doesn't matter for this test
    def sync_function_with_metadata():
        """This is a docstring."""
        pass # pragma: no cover (body doesn't matter for metadata test)
    
    assert sync_function_with_metadata.__name__ == "sync_function_with_metadata"
    assert sync_function_with_metadata.__doc__ == "This is a docstring."

# Test case for a function that raises an exception other than TimeoutException
def test_sync_timeout_propagates_other_exceptions():
    class CustomError(Exception):
        pass

    @timeout(seconds=0.1)
    def sync_function_raises_custom_error():
        # This function does not sleep, so it won't time out
        raise CustomError("Specific error from sync function")

    with pytest.raises(CustomError, match="Specific error from sync function"):
        sync_function_raises_custom_error()

# Test behavior with zero timeout: should expire immediately if any action is taken
def test_sync_timeout_zero_duration_expires_immediately():
    timeout_seconds = 0
    @timeout(seconds=timeout_seconds)
    def sync_function_zero_timeout():
        time.sleep(0.001) # Even a tiny sleep should trigger it if timeout is truly 0
        return "should not return" # pragma: no cover
    
    # The exact behavior for timeout=0 can vary. Some systems might not handle 0 reliably for sleep.
    # For POSIX systems, signal.alarm(0) cancels the alarm.
    # If the implementation uses signal.setitimer, a zero value might also disable the timer.
    # This test assumes that timeout=0 is treated as "expire immediately if not instantaneous".
    # If the library treats 0 as "no timeout", this test needs to change.
    # Or, if it raises ValueError for 0, that's another path.
    # Given typical @timeout implementations using signals, it might raise error on sleep.
    with pytest.raises(TimeoutException, match=f"Timeout expired after {timeout_seconds} seconds"):
         sync_function_zero_timeout()


# Test behavior with negative timeout: should ideally raise ValueError at decoration or call.
def test_sync_timeout_negative_duration_raises_value_error():
    # A common good practice is to raise ValueError for invalid (e.g., negative) timer durations.
    with pytest.raises(ValueError, match="Timeout value must be non-negative"):
        @timeout(seconds=-1)
        def sync_function_negative_timeout():
            pass # pragma: no cover
        sync_function_negative_timeout() # Call to potentially trigger error if not at decoration

# Test with a non-numeric timeout value (e.g. string)
def test_sync_timeout_non_numeric_duration_raises_type_error():
    with pytest.raises(TypeError, match="Timeout value must be a number"):
        @timeout(seconds="invalid")
        def sync_function_non_numeric_timeout():
            pass # pragma: no cover
        sync_function_non_numeric_timeout() # Call to potentially trigger error

# Test function completes very close to the timeout limit (not exceeding)
def test_sync_function_completes_just_before_timeout_limit():
    @timeout(seconds=0.1)
    def sync_function_on_the_edge():
        time.sleep(0.095) # Sleep very close to 0.1s, but not over
        return "edge case success"
    
    assert sync_function_on_the_edge() == "edge case success"

# Test function exceeds very close to the timeout limit
def test_sync_function_exceeds_just_after_timeout_limit():
    timeout_seconds = 0.05
    @timeout(seconds=timeout_seconds)
    def sync_function_just_over_edge():
        time.sleep(timeout_seconds + 0.005) # Sleep just a fraction over
        return "edge case fail" # pragma: no cover
        
    with pytest.raises(TimeoutException, match=f"Timeout expired after {timeout_seconds} seconds"):
        sync_function_just_over_edge()

# Shortened existing async test times and renamed for clarity and consistency.
# Added more specific match strings for TimeoutException.
# Added tests for ValueError on negative timeout and TypeError on non-numeric timeout,
# assuming the decorator performs these validations.
# If these validation tests (ValueError, TypeError) fail, it implies the decorator
# might be less robust in handling invalid input values, but the core functionality tests
# (exceeded, not exceeded) should still provide value.
# Test for timeout=0 assumes it leads to TimeoutException; if it's ValueError or "no timeout", adjust.
# Added `pragma: no cover` for lines that should not be reached if the test logic is correct
# (e.g., after a line that's supposed to raise an exception).
# Made sure to test an async function that *completes* for the async part too.
