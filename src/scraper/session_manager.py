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
