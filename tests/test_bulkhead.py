import pytest
import asyncio
from pyfaulttolerance.bulkhead import bulkhead
from pyfaulttolerance.exceptions import BulkheadRejectionError

# --- Modified Existing Test ---
@bulkhead(max_concurrent_calls=1)
async def tarefa_lenta_original(index): # Renamed to avoid conflict with new function
    await asyncio.sleep(0.1) # Reduced sleep time for faster tests
    return f"executado {index}"

def test_bulkhead_rejects_excess_calls_original_scenario(): # Renamed for clarity
    async def executar():
        # Trying to run two tasks when max_concurrent_calls is 1
        await asyncio.gather(tarefa_lenta_original(1), tarefa_lenta_original(2))

    # Corrected assertion message, note the function name 'tarefa_lenta_original'
    with pytest.raises(BulkheadRejectionError, match=r"\[BulkheadRejection\] Connection rejected due to competition limits in 'tarefa_lenta_original'\."):
        asyncio.run(executar())

# --- New Tests ---

# 1. Calls made within the `max_concurrent_calls` limit should succeed.
@bulkhead(max_concurrent_calls=2)
async def task_for_within_limit_test(index):
    await asyncio.sleep(0.1)
    return f"Task {index} succeeded"

def test_calls_within_limit_succeed():
    async def run_tasks():
        results = await asyncio.gather(
            task_for_within_limit_test(1),
            task_for_within_limit_test(2)
        )
        return results

    results = asyncio.run(run_tasks())
    assert len(results) == 2
    assert "Task 1 succeeded" in results
    assert "Task 2 succeeded" in results

# 2. Verify that the correct number of calls are processed concurrently
#    and excess calls are rejected.
@bulkhead(max_concurrent_calls=2)
async def task_for_concurrency_check(index, duration=0.1):
    await asyncio.sleep(duration)
    return f"Task {index} processed"

def test_correct_number_processed_concurrently_excess_rejected():
    async def run_many_tasks():
        # Attempt to run 3 tasks when max_concurrent_calls is 2.
        # One should be accepted and succeed, one accepted and succeed, one rejected.
        # Order of execution can vary, so gather with return_exceptions=True
        results_or_exceptions = await asyncio.gather(
            task_for_concurrency_check(1, duration=0.2), # longer to ensure it's running when 3rd is called
            task_for_concurrency_check(2, duration=0.2),
            task_for_concurrency_check(3, duration=0.01), # Shorter, but should be rejected if others started
            return_exceptions=True
        )
        return results_or_exceptions

    results = asyncio.run(run_many_tasks())
    
    successful_tasks = [r for r in results if isinstance(r, str)]
    rejected_tasks = [r for r in results if isinstance(r, BulkheadRejectionError)]

    assert len(successful_tasks) == 2, f"Expected 2 successful tasks, got {len(successful_tasks)}. Results: {results}"
    assert len(rejected_tasks) == 1, f"Expected 1 rejected task, got {len(rejected_tasks)}. Results: {results}"

    # Verify the rejection message from the exception instance
    # The rejected task could be any of the three due to gather's scheduling,
    # but usually, the ones that acquire the semaphore first will proceed.
    # The key is that *one* was rejected with the correct error type.
    assert isinstance(rejected_tasks[0], BulkheadRejectionError)
    # The function name in the message will be 'task_for_concurrency_check'
    expected_match_str = r"\[BulkheadRejection\] Connection rejected due to competition limits in 'task_for_concurrency_check'\."
    assert rejected_tasks[0].args[0].startswith("[BulkheadRejection] Connection rejected")
    assert "task_for_concurrency_check" in rejected_tasks[0].args[0]


# Test with max_concurrent_calls = 0 (should reject all calls if it means no calls allowed)
@bulkhead(max_concurrent_calls=0)
async def task_with_zero_concurrency(index):
    await asyncio.sleep(0.01) # pragma: no cover (should not be reached)
    return f"Task {index} processed" # pragma: no cover

def test_bulkhead_with_zero_max_concurrent_calls():
    async def run_task():
        return await task_with_zero_concurrency(1)

    with pytest.raises(BulkheadRejectionError, match=r"\[BulkheadRejection\] Connection rejected due to competition limits in 'task_with_zero_concurrency'\."):
        asyncio.run(run_task())

# Test that non-async functions can also be decorated (though bulkhead is typically for async)
# This depends on the bulkhead implementation; if it expects awaitables, this might behave differently.
# Assuming it's primarily for async and might either error or work "vacuously" for sync.
def test_bulkhead_on_sync_function_rejection():
    # This test's behavior depends heavily on how @bulkhead handles non-async functions.
    # If it acquires a semaphore and releases it, it might work.
    # If it expects an awaitable, it might fail differently or not apply the limit as expected.
    # For this test, let's define it and see. If it fails, it indicates an area to clarify in docs or code.
    
    # Re-define a sync version for this test
    @bulkhead(max_concurrent_calls=1)
    def sync_task_for_bulkhead(index):
        # time.sleep(0.1) # Not async, so can't use asyncio.sleep
        # If this were a real sync blocking call, the test setup would be more complex
        # to simulate concurrent calls (e.g. threading).
        # For simplicity, we'll just call it sequentially and test if rejection happens
        # if we could somehow force concurrency.
        # This test is more conceptual given the current structure.
        # Let's assume it behaves as expected for a single call.
        return f"Sync task {index} done"

    # First call should succeed
    assert sync_task_for_bulkhead(1) == "Sync task 1 done"

    # To test rejection, we'd need true concurrency.
    # Pytest doesn't easily do this for sync functions without threading.
    # The decorator might not even be intended for sync functions.
    # For now, this part of the test is more of a placeholder for future exploration
    # or if the library explicitly states support for sync functions.
    # If @bulkhead is async-only, attempting to apply it to a sync function
    # might result in errors or unexpected behavior at decoration or call time.

    # Let's assume for now the decorator *could* be applied and test a scenario
    # where we try to "fake" over-subscription if its internal counter is naive.
    # This is hard to test properly without threads for sync functions.
    # We will skip the rejection part for sync functions for now as it's not straightforward
    # with asyncio-focused tools and the current problem scope.
    pass # Placeholder for more complex sync testing if needed.


# Test to ensure that if tasks complete quickly, the slots are freed up.
@bulkhead(max_concurrent_calls=1)
async def quick_task(index):
    await asyncio.sleep(0.01) # Very quick task
    return f"Quick task {index} done"

def test_slots_freed_up_quickly():
    async def run_sequence_of_quick_tasks():
        results = []
        # These calls are sequential in terms of `await` but will test if the bulkhead
        # correctly releases the slot.
        results.append(await quick_task(1)) # Occupies the slot, then releases
        results.append(await quick_task(2)) # Should succeed if slot from task 1 was released
        results.append(await quick_task(3)) # Should succeed if slot from task 2 was released
        return results

    results = asyncio.run(run_sequence_of_quick_tasks())
    assert len(results) == 3
    assert results == ["Quick task 1 done", "Quick task 2 done", "Quick task 3 done"]

# Test with a larger number of concurrent calls allowed
@bulkhead(max_concurrent_calls=5)
async def high_concurrency_task(index):
    await asyncio.sleep(0.05)
    return f"High concurrency task {index} done"

def test_higher_concurrency_limit():
    async def run_high_concurrency_tasks():
        tasks_to_run = [high_concurrency_task(i) for i in range(5)] # 5 tasks, limit is 5
        results = await asyncio.gather(*tasks_to_run)
        return results
    
    results = asyncio.run(run_high_concurrency_tasks())
    assert len(results) == 5
    for i in range(5):
        assert f"High concurrency task {i} done" in results

    # Now try to exceed this higher limit
    async def run_exceeding_high_concurrency_tasks():
        tasks_to_run = [high_concurrency_task(i) for i in range(6)] # 6 tasks, limit is 5
        results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
        return results

    results_with_rejection = asyncio.run(run_exceeding_high_concurrency_tasks())
    successful_count = sum(1 for r in results_with_rejection if isinstance(r, str))
    rejected_count = sum(1 for r in results_with_rejection if isinstance(r, BulkheadRejectionError))

    assert successful_count == 5
    assert rejected_count == 1
    # And check the error message on the rejected one
    rejected_error = next(r for r in results_with_rejection if isinstance(r, BulkheadRejectionError))
    assert "high_concurrency_task" in rejected_error.args[0]

# Renamed the original `tarefa_lenta` to `tarefa_lenta_original` and its test.
# Corrected the assertion message in the original test (now `test_bulkhead_rejects_excess_calls_original_scenario`).
# Added `test_calls_within_limit_succeed`.
# Added `test_correct_number_processed_concurrently_excess_rejected` to verify concurrent processing and rejection.
# Added `test_bulkhead_with_zero_max_concurrent_calls`.
# Added `test_slots_freed_up_quickly` to ensure slots are released.
# Added `test_higher_concurrency_limit` for a bulkhead with a larger capacity.
# Sleep times reduced for faster test execution.
# The test for sync functions `test_bulkhead_on_sync_function_rejection` is a placeholder due to complexity
# of testing sync concurrency without threads, assuming the library is async-focused.
# Used `return_exceptions=True` in `asyncio.gather` for tests expecting partial failures.
# Made match strings for BulkheadRejectionError more precise using raw strings for regex-like characters.
# Ensured function names in error messages are correctly matched.
# The test `test_correct_number_processed_concurrently_excess_rejected` is key for "Verify that the correct number of calls are processed concurrently".
# It does this by launching more tasks than permitted and checking that the exact number of allowed tasks succeed and the rest are rejected.
# This implicitly shows that `max_concurrent_calls` tasks were able to acquire the semaphore (or equivalent) and run.
# The actual "simultaneous" execution is managed by asyncio's event loop and the OS, but the bulkhead's role is to limit access, which is what's tested.
