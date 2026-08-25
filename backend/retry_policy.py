import time
import random
import functools
import logging
from typing import Callable, Any, Type, Tuple, Optional

logger = logging.getLogger(__name__)

# Task 11: Explicit Error Classification
RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    TimeoutError,
    ConnectionError,
    OSError,
)

NON_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ValueError,
    KeyError,
    TypeError,
    PermissionError,
)

class RetryPolicy:
    """Task 11 & Task 12: Comprehensive Retry Policy with Exponential Backoff & Jitter."""
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 0.1,
        max_delay: float = 5.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def is_retryable(self, exception: Exception) -> bool:
        """Task 11: Determine if an exception is retryable."""
        if isinstance(exception, NON_RETRYABLE_EXCEPTIONS):
            return False
        if isinstance(exception, RETRYABLE_EXCEPTIONS):
            return True
        # Check HTTP status codes if available
        status_code = getattr(exception, "status_code", None)
        if status_code is not None:
            if status_code in (429, 502, 503, 504):
                return True
            if 400 <= status_code < 500:
                return False
        return True

    def calculate_backoff(self, attempt: int) -> float:
        """Task 12: Calculate exponential backoff delay with random jitter."""
        delay = min(self.max_delay, self.initial_delay * (self.backoff_factor ** attempt))
        if self.jitter:
            delay += random.uniform(0, 0.1 * delay)
        return delay

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute callable with retry policy and backoff."""
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries and self.is_retryable(e):
                    backoff = self.calculate_backoff(attempt)
                    logger.warning(f"Retryable error on attempt {attempt+1}/{self.max_retries}: {e}. Retrying in {backoff:.2f}s...")
                    time.sleep(backoff)
                else:
                    raise e
        if last_exception:
            raise last_exception

# Task 13: Operation Timeout Helper
def execute_with_timeout(func: Callable, timeout_seconds: float = 10.0, *args, **kwargs) -> Any:
    """Task 13: Timeout wrapper for external operations."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds.")
