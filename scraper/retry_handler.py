from dataclasses import dataclass
from typing import Callable, Optional, Any
import time
import logging

logger = logging.getLogger("scraper.retry")

@dataclass
class RetryPolicy:
    initial_delay: float = 1.0
    multiplier: float = 2.0
    max_attempts: int = 4
    max_delay: float = 60.0

def with_retry(func: Callable[[], Any], policy: RetryPolicy, on_retry: Optional[Callable[[int, float, Exception], None]] = None) -> Any:
    \"\"\"Execute func with exponential backoff retry logic.

    func: zero-arg callable that may raise exceptions on failure.
    policy: RetryPolicy controlling delays and attempts.
    on_retry: optional callback(attempt_number, delay_seconds, exception) for observability.
    \"\"\"
    attempt = 0
    delay = policy.initial_delay
    last_exc: Optional[Exception] = None

    while attempt < policy.max_attempts:
        try:
            return func()
        except Exception as e:
            last_exc = e
            attempt += 1
            # If we've exhausted attempts, re-raise the last exception
            if attempt >= policy.max_attempts:
                logger.error(\"with_retry: max attempts reached; re-raising\")
                raise

            # Call optional callback for instrumentation
            if on_retry:
                try:
                    on_retry(attempt, delay, e)
                except Exception:
                    logger.exception(\"with_retry: on_retry callback raised an exception\")

            logger.warning(f\"Retry {attempt}/{policy.max_attempts} after {delay}s: {e}\")
            time.sleep(delay)
            delay = min(delay * policy.multiplier, policy.max_delay)

    # Defensive: if loop exits unexpectedly, raise last seen exception
    if last_exc:
        raise last_exc
    return None