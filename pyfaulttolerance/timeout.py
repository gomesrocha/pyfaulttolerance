# app/timeout.py
import signal
import functools

class TimeoutException(Exception): pass

def timeout(seconds=5):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutException("Function timed out")

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
        return wrapper
    return decorator
