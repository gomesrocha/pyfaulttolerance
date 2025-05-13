class FaultToleranceError(Exception):
    """Exceção base para o pyfaulttolerance."""

class TimeoutError(FaultToleranceError):
    def __init__(self, function_name):
        super().__init__(f"[TimeoutError] Function '{function_name}' has exceeded the time limit.")

class CircuitBreakerOpenError(FaultToleranceError):
    def __init__(self, function_name):
        super().__init__(f"[CircuitBreakerOpen] Open circuit for function '{function_name}'.")

class BulkheadRejectionError(FaultToleranceError):
    def __init__(self, function_name):
        super().__init__(f"[BulkheadRejection] Connection rejected due to competition limits in '{function_name}'.")

class RetryExceededError(FaultToleranceError):
    def __init__(self, function_name, attempts):
        super().__init__(f"[RetryExceeded] Failed after {attempts} in '{function_name}'.")
