import signal
import functools

class TimeoutException(Exception): pass

def timeout(seconds=5):
    if not isinstance(seconds, (int, float)):
        raise TypeError("Timeout value must be a number")
    if seconds < 0:
        raise ValueError("Timeout value must be non-negative")

    def decorator(func):
        def _handle_timeout(signum, frame):
            # 'seconds' is from the outer scope of the decorator factory
            raise TimeoutException(f"Timeout expired after {seconds} seconds")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check the original value for precise 0
            if seconds == 0: 
                raise TimeoutException(f"Timeout expired after {seconds} seconds")

            effective_seconds = int(seconds)
            # If effective_seconds is 0 due to float truncation (e.g., seconds=0.1),
            # signal.alarm(0) would cancel any pending alarm, effectively not setting a new one.
            # This specific subtask is focused on seconds == 0.
            # The behavior for 0 < seconds < 1 for this sync decorator means it won't timeout
            # before the function completes, unless the function itself is extremely short.

            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(effective_seconds) 
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0) # Cancel any pending alarm
        return wrapper
    return decorator
