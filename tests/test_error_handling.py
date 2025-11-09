# tests/test_error_handling.py
"""Test error handling and retry logic."""

import pytest
import asyncio
from src.shared.rate_limiter import RateLimiter
from src.scraper.session_manager import SessionManager


@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter enforces minimum interval."""
    limiter = RateLimiter(min_interval=2)

    start = asyncio.get_event_loop().time()
    await limiter.wait_if_needed()
    await limiter.wait_if_needed()
    elapsed = asyncio.get_event_loop().time() - start

    assert elapsed >= 2.0  # Second call should wait 2 seconds


def test_session_manager_timeout():
    """Test session timeout detection."""
    manager = SessionManager(session_timeout_minutes=0)
    manager.update_activity()

    import time
    time.sleep(0.1)

    assert not manager.is_alive()  # Should timeout immediately


def test_session_manager_alive():
    """Test session manager correctly identifies active session."""
    manager = SessionManager(session_timeout_minutes=60)
    manager.update_activity()

    assert manager.is_alive()  # Should still be alive
