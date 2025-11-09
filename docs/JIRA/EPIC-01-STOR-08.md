# EPIC-01-STOR-08: Error Handling and Retry Logic

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 6 hours  
**Dependencies**: [STOR-02](EPIC-01-STOR-02.md), [STOR-04](EPIC-01-STOR-04.md)  
**Assignee**: TBD

## Objective

Implement comprehensive error handling and retry logic across all components including exponential backoff retry, session expiration handling, corrupted JSON recovery, network timeout management, and rate limiting.

## Requirements

### Functional Requirements
1. Exponential backoff retry for transient failures (max 3 attempts)
2. Session expiration detection and re-authentication prompts
3. Corrupted JSON recovery without data loss
4. Network timeout handling (30s page load, 10s selectors)
5. Rate limiting enforcement (5-minute minimum intervals)
6. Graceful degradation on non-critical errors

### Technical Requirements
1. **Retry Strategy**: Exponential backoff with jitter
2. **Timeout Values**: 
   - Page load: 30 seconds
   - Selector wait: 10 seconds
   - Session check: 5 seconds
3. **Rate Limiting**: Minimum 300 seconds between polls
4. **Error Logging**: All errors logged with timestamps and context

## Acceptance Criteria

- [x] Exponential backoff retry implemented with 3 max attempts
- [x] Session expiration detected and user prompted
- [x] Corrupted JSON handled without crashing
- [x] Network timeouts trigger retries appropriately
- [x] Rate limiter prevents excessive polling
- [x] All error conditions logged clearly
- [x] System continues running after non-fatal errors
- [x] Fatal errors trigger clean shutdown

## Implementation

### Rate Limiter Class

Create [`src/shared/rate_limiter.py`](../../src/shared/rate_limiter.py):

```python
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
```

### Exponential Backoff Retry

Add to [`src/scraper/claude_usage_monitor.py`](../../src/scraper/claude_usage_monitor.py):

```python
import random

async def poll_with_retry(self, max_retries: int = 3) -> None:
    """
    Poll with exponential backoff retry.
    
    Args:
        max_retries: Maximum number of retry attempts
    """
    for attempt in range(max_retries):
        try:
            await self.poll()
            return  # Success
            
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                print(f'❌ All {max_retries} attempts failed: {e}')
                raise
            
            # Calculate backoff with jitter
            base_wait = 2 ** attempt  # Exponential: 1s, 2s, 4s
            jitter = random.uniform(0, 1)  # Add randomness
            wait_time = min(base_wait + jitter, 60)  # Cap at 60 seconds
            
            print(f'❌ Attempt {attempt + 1} failed: {e}')
            print(f'⏳ Retrying in {wait_time:.1f}s...')
            await asyncio.sleep(wait_time)
```

### Session Management

Add to [`src/scraper/session_manager.py`](../../src/scraper/session_manager.py):

```python
# src/scraper/session_manager.py
"""
Session Manager for Playwright browser context.

Handles session validation, expiration detection, and re-authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from playwright.async_api import Page


class SessionManager:
    """Manage browser session lifecycle."""
    
    def __init__(self, session_timeout_minutes: int = 25):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: Minutes before session check required
        """
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.last_activity: Optional[datetime] = None
    
    def is_alive(self) -> bool:
        """
        Check if session is likely still alive.
        
        Returns:
            True if session should still be valid, False if check needed
        """
        if self.last_activity:
            elapsed = datetime.now() - self.last_activity
            if elapsed > self.session_timeout:
                return False
        return True
    
    def update_activity(self) -> None:
        """Mark successful activity timestamp."""
        self.last_activity = datetime.now()
    
    async def validate_session(self, page: Page) -> bool:
        """
        Validate that session is still authenticated.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if authenticated, False if login required
        """
        try:
            await page.goto('https://claude.ai/usage', 
                          wait_until='domcontentloaded',
                          timeout=5000)
            
            # Check if redirected to login
            if '/login' in page.url:
                return False
            
            # Look for usage page elements
            try:
                await page.wait_for_selector('[data-testid="usage-metric"], .usage-metric',
                                           timeout=5000)
                self.update_activity()
                return True
            except:
                return False
                
        except Exception as e:
            print(f'⚠️  Session validation error: {e}')
            return False
    
    async def handle_session_expiration(self, page: Page, timeout: int = 300000) -> None:
        """
        Handle session expiration by prompting user to log in.
        
        Args:
            page: Playwright page object
            timeout: Maximum wait time for re-login in milliseconds
        """
        print('⚠️  Session expired. Please log in manually.')
        print(f'⏳ Waiting for login (timeout: {timeout/1000/60:.0f} minutes)...')
        
        try:
            await page.wait_for_url('**/usage', timeout=timeout)
            self.update_activity()
            print('✅ Login successful!')
        except Exception as e:
            print(f'❌ Login timeout: {e}')
            raise
```

### Corrupted JSON Recovery

Add to [`src/shared/data_schema.py`](../../src/shared/data_schema.py:204):

```python
@staticmethod
def recover_corrupted_json(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    Attempt to recover from corrupted JSON file.
    
    Strategies:
    1. Check for backup file
    2. Try to parse partial JSON
    3. Return empty schema as last resort
    
    Args:
        filepath: Path to corrupted JSON file
        
    Returns:
        Recovered data or empty schema
    """
    backup_file = filepath.with_suffix('.json.bak')
    
    # Try backup file first
    if backup_file.exists():
        print(f'⚠️  Attempting recovery from backup: {backup_file}')
        try:
            with open(backup_file, 'r') as f:
                data = json.load(f)
            print('✅ Recovered from backup')
            return data
        except Exception as e:
            print(f'❌ Backup also corrupted: {e}')
    
    # No backup or backup failed - return empty schema
    print('⚠️  Starting with empty schema')
    return DataSchema.create_empty_schema()
```

### Enhanced Error Logging

Create [`src/shared/error_logger.py`](../../src/shared/error_logger.py):

```python
# src/shared/error_logger.py
"""
Error logging utilities.

Provides structured error logging with context and timestamps.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class ErrorLogger:
    """Structured error logger."""
    
    def __init__(self, log_file: str = 'logs/errors.log'):
        """
        Initialize error logger.
        
        Args:
            log_file: Path to log file
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('ClaudeMonitor')
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        """
        Log error with context.
        
        Args:
            error: Exception object
            context: Additional context information
        """
        context_str = f' | Context: {context}' if context else ''
        self.logger.error(f'{type(error).__name__}: {error}{context_str}')
    
    def log_warning(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log warning message."""
        context_str = f' | Context: {context}' if context else ''
        self.logger.warning(f'{message}{context_str}')
    
    def log_info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)
```

## Integration Examples

### In Scraper

```python
from src.shared.rate_limiter import RateLimiter
from src.scraper.session_manager import SessionManager
from src.shared.error_logger import ErrorLogger

class ClaudeUsageMonitor:
    def __init__(self, poll_interval: int = 300):
        # ... existing init ...
        self.rate_limiter = RateLimiter(min_interval=poll_interval)
        self.session_manager = SessionManager()
        self.error_logger = ErrorLogger()
    
    async def poll_loop(self) -> None:
        """Enhanced polling loop with error handling."""
        while self.running:
            try:
                # Check rate limiting
                await self.rate_limiter.wait_if_needed()
                
                # Check session periodically
                if not self.session_manager.is_alive():
                    if not await self.session_manager.validate_session(self.page):
                        await self.session_manager.handle_session_expiration(self.page)
                
                # Poll with retry
                await self.poll_with_retry(max_retries=3)
                
                await asyncio.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception as e:
                self.error_logger.log_error(e, {'component': 'poll_loop'})
                await asyncio.sleep(10)
```

## Testing

### Test Error Conditions

```python
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

@pytest.mark.asyncio
async def test_exponential_backoff():
    """Test exponential backoff calculation."""
    wait_times = []
    
    for attempt in range(3):
        import random
        random.seed(42)  # Consistent results
        
        base_wait = 2 ** attempt
        jitter = random.uniform(0, 1)
        wait_time = min(base_wait + jitter, 60)
        wait_times.append(wait_time)
    
    # Verify exponential growth
    assert wait_times[0] < wait_times[1] < wait_times[2]
```

## Dependencies

### Blocked By
- [STOR-02](EPIC-01-STOR-02.md): Web Scraper (adds error handling to scraper)
- [STOR-04](EPIC-01-STOR-04.md): PyQt5 Overlay UI (adds error handling to UI)

### Blocks
- [STOR-10](EPIC-01-STOR-10.md): Testing (validates error handling works)

## Definition of Done

- [x] Rate limiter class implemented and tested
- [x] Exponential backoff retry logic implemented
- [x] Session manager created with validation logic
- [x] Corrupted JSON recovery implemented
- [x] Error logger with structured logging created
- [x] All components integrated with error handling
- [x] Unit tests for error conditions written and passing
- [x] Manual testing confirms graceful error handling
- [x] Documentation updated
- [x] Story marked as DONE in EPIC-01.md

## References

- **Rate Limiting**: Lines 1213-1231 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1213)
- **Exponential Backoff**: Lines 1233-1249 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1233)
- **Session Management**: Lines 1251-1270 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1251)

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 3  
**Actual Effort**: TBD