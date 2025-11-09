# src/shared/rate_limiter.py
"""
Rate Limiter for polling operations.

Ensures minimum interval between requests to prevent rate limiting
and respect server resources.
"""

import asyncio
from datetime import datetime
from typing import Optional


class RateLimiter:
    """Enforce minimum interval between operations."""

    def __init__(self, min_interval: int = 300):
        """
        Initialize rate limiter.

        Args:
            min_interval: Minimum seconds between operations (default 300 = 5 minutes)
        """
        self.min_interval = min_interval
        self.last_request: Optional[datetime] = None

    async def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        if self.last_request:
            elapsed = (datetime.now() - self.last_request).total_seconds()

            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                print(f'⏳ Rate limiting: waiting {wait_time:.0f}s before next poll')
                await asyncio.sleep(wait_time)

        self.last_request = datetime.now()

    def reset(self) -> None:
        """Reset rate limiter (allow immediate next request)."""
        self.last_request = None
