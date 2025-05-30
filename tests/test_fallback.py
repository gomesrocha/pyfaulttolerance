from pyfaulttolerance.fallback import fallback
import asyncio
import pytest

# --- Existing Test ---
# Função de fallback que será usada quando a principal falhar
async def fallback_func():
    return "fallback value"

# Função principal que sempre falha
@fallback(fallback_func)
async def always_fail():
    raise Exception("Simulated error")

def test_fallback_existing(): # Renamed to avoid collision
    result = asyncio.run(always_fail())
    assert result == "fallback value"

# --- New Tests ---

# Custom Exceptions for clarity
class MainException(Exception):
    pass

class FallbackException(Exception):
    pass

# Helper functions for tests

# Synchronous main functions
def sync_main_succeeds():
    return "sync main success"

def sync_main_fails():
    raise MainException("Sync main failed")

# Asynchronous main functions
async def async_main_succeeds():
    await asyncio.sleep(0) # Ensure it's a coroutine
    return "async main success"

async def async_main_fails():
    await asyncio.sleep(0)
    raise MainException("Async main failed")

# Synchronous fallback functions
def sync_fallback_succeeds():
    return "sync fallback success"

def sync_fallback_fails():
    raise FallbackException("Sync fallback failed")

# Asynchronous fallback functions
async def async_fallback_succeeds():
    await asyncio.sleep(0)
    return "async fallback success"

async def async_fallback_fails():
    await asyncio.sleep(0)
    raise FallbackException("Async fallback failed")


# 1. Synchronous main function with a synchronous fallback function
@fallback(sync_fallback_succeeds)
def sync_main_fails_with_sync_fallback():
    return sync_main_fails()

@fallback(sync_fallback_succeeds)
def sync_main_succeeds_with_sync_fallback():
    return sync_main_succeeds()

def test_sync_main_fails_sync_fallback_called():
    result = sync_main_fails_with_sync_fallback()
    assert result == "sync fallback success"

def test_sync_main_succeeds_sync_fallback_not_called():
    result = sync_main_succeeds_with_sync_fallback()
    assert result == "sync main success"


# 2. Asynchronous main function with a synchronous fallback function
@fallback(sync_fallback_succeeds)
async def async_main_fails_with_sync_fallback():
    return await async_main_fails()

@fallback(sync_fallback_succeeds)
async def async_main_succeeds_with_sync_fallback():
    return await async_main_succeeds()

def test_async_main_fails_sync_fallback_called():
    result = asyncio.run(async_main_fails_with_sync_fallback())
    assert result == "sync fallback success"

def test_async_main_succeeds_sync_fallback_not_called():
    result = asyncio.run(async_main_succeeds_with_sync_fallback())
    assert result == "async main success"


# 3. Synchronous main function with an asynchronous fallback function
@fallback(async_fallback_succeeds)
def sync_main_fails_with_async_fallback():
    return sync_main_fails()

@fallback(async_fallback_succeeds)
def sync_main_succeeds_with_async_fallback():
    return sync_main_succeeds()

def test_sync_main_fails_async_fallback_called():
    # Fallback is async, so the decorated function becomes async
    result = asyncio.run(sync_main_fails_with_async_fallback())
    assert result == "async fallback success"

def test_sync_main_succeeds_async_fallback_not_called():
    # Main is sync and succeeds, so no async fallback is run
    result = sync_main_succeeds_with_async_fallback()
    assert result == "sync main success"


# 4. Scenario where the main async function fails AND the async fallback function also fails
@fallback(async_fallback_fails)
async def async_main_fails_with_failing_async_fallback():
    return await async_main_fails()

def test_async_main_fails_async_fallback_fails():
    with pytest.raises(FallbackException, match="Async fallback failed"):
        asyncio.run(async_main_fails_with_failing_async_fallback())


# 5. Scenario where the main sync function fails AND the sync fallback function also fails
@fallback(sync_fallback_fails)
def sync_main_fails_with_failing_sync_fallback():
    return sync_main_fails()

def test_sync_main_fails_sync_fallback_fails():
    with pytest.raises(FallbackException, match="Sync fallback failed"):
        sync_main_fails_with_failing_sync_fallback()


# 6. Scenario where the main async function fails AND the sync fallback function also fails
@fallback(sync_fallback_fails)
async def async_main_fails_with_failing_sync_fallback():
    return await async_main_fails()

def test_async_main_fails_sync_fallback_fails():
    with pytest.raises(FallbackException, match="Sync fallback failed"):
        asyncio.run(async_main_fails_with_failing_sync_fallback())


# 7. Scenario where the main sync function fails AND the async fallback function also fails
@fallback(async_fallback_fails)
def sync_main_fails_with_failing_async_fallback():
    # If main is sync and fallback is async, the wrapper becomes async
    return sync_main_fails()

def test_sync_main_fails_async_fallback_fails():
    with pytest.raises(FallbackException, match="Async fallback failed"):
        asyncio.run(sync_main_fails_with_failing_async_fallback())

# Ensure that if main is sync and fallback is async, and main succeeds, it doesn't run fallback
@fallback(async_fallback_succeeds)
def sync_main_succeeds_with_async_fallback_check_no_await():
    return sync_main_succeeds()

def test_sync_main_succeeds_async_fallback_not_called_direct_return():
    result = sync_main_succeeds_with_async_fallback_check_no_await()
    assert result == "sync main success"
    # Further check: result should not be a coroutine
    assert not asyncio.iscoroutine(result)

# Test case: what if the fallback_func argument is not callable?
def test_fallback_with_non_callable_fallback_func():
    with pytest.raises(TypeError, match="'NoneType' object is not callable"): # Or a more specific error from the decorator
        @fallback(None)
        def function_with_invalid_fallback():
            raise Exception("Should not matter")
        function_with_invalid_fallback()

# Test case: main async, fallback sync, main success
@fallback(sync_fallback_succeeds)
async def async_main_succeeds_ensure_no_fallback_run():
    return await async_main_succeeds()

async def test_async_main_succeeds_sync_fallback_not_called_async_test():
    result = await async_main_succeeds_ensure_no_fallback_run()
    assert result == "async main success"

# Test case: main sync, fallback async, main success
@fallback(async_fallback_succeeds)
def sync_main_succeeds_ensure_no_fallback_run():
    return sync_main_succeeds()

# This test needs to be async if we want to use pytest-asyncio properly for it
# However, the function itself sync_main_succeeds_ensure_no_fallback_run
# will return a value directly if the main sync function succeeds,
# it does not become a coroutine in that case.
def test_sync_main_succeeds_async_fallback_not_called_direct_return_value():
    result = sync_main_succeeds_ensure_no_fallback_run()
    assert result == "sync main success"
    assert not asyncio.iscoroutine(result)

# Test for when fallback is async and main is sync and fails (original test_sync_main_fails_async_fallback_called is fine)
# This is just to be super sure about the execution model
@fallback(async_fallback_succeeds)
def sync_main_fails_for_async_fb_wrapper_check():
    raise MainException("sync main failed for async fb check")

async def test_sync_main_fails_async_fallback_is_awaited():
    result = await sync_main_fails_for_async_fb_wrapper_check() # The wrapper should return a coroutine
    assert result == "async fallback success"

# Test for when fallback is sync and main is async and fails (original test_async_main_fails_sync_fallback_called is fine)
# This is to be sure about the execution model
@fallback(sync_fallback_succeeds)
async def async_main_fails_for_sync_fb_wrapper_check():
    raise MainException("async main failed for sync fb check")

async def test_async_main_fails_sync_fallback_is_awaited():
    result = await async_main_fails_for_sync_fb_wrapper_check()
    assert result == "sync fallback success"

# Test that the original value is returned if no exception occurs (async main, async fallback)
@fallback(async_fallback_succeeds)
async def async_main_succeeds_with_async_fallback():
    return await async_main_succeeds()

async def test_async_main_succeeds_async_fallback_not_called():
    result = await async_main_succeeds_with_async_fallback()
    assert result == "async main success"

# Test that the original value is returned if no exception occurs (sync main, sync fallback)
# This is covered by test_sync_main_succeeds_sync_fallback_not_called

# Test that the original value is returned if no exception occurs (async main, sync fallback)
# This is covered by test_async_main_succeeds_sync_fallback_not_called (needs asyncio.run)

# Test that the original value is returned if no exception occurs (sync main, async fallback)
# This is covered by test_sync_main_succeeds_async_fallback_not_called_direct_return_value
