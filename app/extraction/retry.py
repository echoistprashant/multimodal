"""Exponential Backoff and Jitter Retry Handler.

Provides resilient async retry execution for transient network errors,
API rate limit throttling (HTTP 429), and remote inference timeouts.
"""

import asyncio
import random
from typing import Any, Awaitable, Callable, Tuple, Type
from app.core.logging import get_logger

logger = get_logger("app.extraction.retry")


async def retry_with_backoff(
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    max_retries: int = 3,
    initial_delay_sec: float = 0.25,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """Execute async callable with exponential backoff and randomized jitter.

    Args:
        func: Async function to execute.
        max_retries: Maximum number of retry attempts before propagating the error.
        initial_delay_sec: Base sleep duration before the first retry.
        backoff_factor: Multiplier applied per consecutive failure.
        retryable_exceptions: Tuple of exception types to catch and retry.

    Returns:
        Result of the successful invocation.
    """
    attempt = 0
    while True:
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as err:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Function {func.__name__} exhausted {max_retries} retries: {err}")
                raise

            # Exponential backoff + uniform jitter (Full Jitter strategy)
            delay = (initial_delay_sec * (backoff_factor ** (attempt - 1))) + random.uniform(0.01, 0.05)
            logger.warning(
                f"Attempt {attempt}/{max_retries} failed for {func.__name__} ({err}). Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)
