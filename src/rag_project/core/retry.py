"""
Retry logic with exponential backoff for OpenAI and ChromaDB calls.
"""

from __future__ import annotations

import time
import functools
from typing import Callable, Type, Tuple

from ..logging_config import get_logger

logger = get_logger("retry")

# Default retryable exceptions
RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)

# Add OpenAI-specific exceptions if available
try:
    from openai import APITimeoutError, APIConnectionError, RateLimitError, InternalServerError
    RETRYABLE_EXCEPTIONS = RETRYABLE_EXCEPTIONS + (
        APITimeoutError,
        APIConnectionError,
        RateLimitError,
        InternalServerError,
    )
except ImportError:
    pass


def retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = RETRYABLE_EXCEPTIONS,
) -> Callable:
    """
    Decorator: retry with exponential backoff.

    Usage:
        @retry(max_retries=3)
        def call_openai(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            "Failed after %d retries: %s — %s",
                            max_retries, func.__name__, e,
                        )
                        raise
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    logger.warning(
                        "Retry %d/%d for %s after %.1fs — %s: %s",
                        attempt + 1, max_retries, func.__name__, delay,
                        type(e).__name__, e,
                    )
                    time.sleep(delay)
            raise last_exception  # type: ignore[misc]
        return wrapper
    return decorator
