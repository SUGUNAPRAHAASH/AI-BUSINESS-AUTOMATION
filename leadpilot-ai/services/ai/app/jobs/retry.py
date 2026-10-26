import asyncio
import random
import time
from typing import Callable, Any
from app.utils.logging import logger


async def retry_with_backoff(
    coro_func: Callable[[], Any],
    max_attempts: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    jitter: bool = True
) -> Any:
    """
    Execute coroutine with exponential backoff and jitter.
    Retries only on transient network/server errors.
    """
    attempt = 0
    delay = initial_delay

    while True:
        attempt += 1
        try:
            return await coro_func()
        except Exception as e:
            if attempt >= max_attempts:
                logger.error(f"Retry exhausted after {attempt} attempts: {e}")
                raise e

            sleep_time = delay * (1 + (random.random() * 0.2 if jitter else 0))
            logger.warning(f"Attempt {attempt} failed ({e}). Retrying in {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)
            delay *= backoff_factor
