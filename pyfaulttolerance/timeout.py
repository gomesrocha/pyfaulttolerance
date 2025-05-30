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
            if seconds == 0:
                raise TimeoutException(f"Timeout expired after {seconds} seconds")

            # For positive timeouts, signal.alarm requires integers.
            # If seconds is > 0 and < 1, int(seconds) would be 0,
            # which cancels the alarm. So, use 1 second as the minimum effective timeout.
            if 0 < seconds < 1:
                effective_seconds = 1
            else:
                effective_seconds = int(seconds) # For seconds >= 1 or if seconds is a whole number float

            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(effective_seconds)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)  # Cancel any pending alarm
        return wrapper
    return decorator
