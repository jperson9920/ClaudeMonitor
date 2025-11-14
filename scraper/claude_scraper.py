#!/usr/bin/env python3
"""
Claude.ai Usage Scraper
Monitors claude.ai/settings/usage page to extract usage metrics
Uses undetected-chromedriver to bypass Cloudflare protection
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import sys
from pathlib import Path
import logging
import re
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stderr)  # Errors to stderr, data to stdout
    ]
)
logger = logging.getLogger(__name__)


class ClaudeUsageScraper:
    """Scrapes usage data from claude.ai/settings/usage page"""

    def __init__(self, profile_dir='./chrome-profile'):
        """
        Initialize scraper with persistent browser profile

        Args:
            profile_dir: Directory to store browser profile and cookies
        """
        self.profile_dir = Path(profile_dir).resolve()
        self.profile_dir.mkdir(exist_ok=True)
        self.driver = None
        self.session_file = self.profile_dir / 'session.json'
        logger.info(f"Initialized ClaudeUsageScraper with profile dir: {self.profile_dir}")

    def create_driver(self):
        """
        Create Chrome driver with anti-detection configuration

        Returns:
            WebDriver instance configured for Cloudflare bypass
        """
        logger.info("Creating Chrome driver with anti-detection measures")

        options = uc.ChromeOptions()

        # CRITICAL: Use persistent profile for session management
        options.add_argument(f'--user-data-dir={self.profile_dir}')
        options.add_argument('--profile-directory=Default')

        # Anti-detection measures
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-web-security')

        # Realistic window size
        options.add_argument('--window-size=1920,1080')

        try:
            # CRITICAL: headless=False for better Cloudflare bypass
            # use_subprocess=True for stability
            self.driver = uc.Chrome(
                options=options,
                headless=False,  # Must be False for high success rate
                use_subprocess=True,
                version_main=None  # Auto-detect Chrome version
            )

            # Set realistic timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

            logger.info("Chrome driver created successfully")
            return self.driver

        except Exception as e:
            logger.error(f"Failed to create Chrome driver: {e}")
            raise

    def manual_login(self):
        """
        One-time manual login to establish session
        User completes login, then session is saved for future use

        Returns:
            bool: True if login successful and session saved
        """
        if not self.driver:
            self.create_driver()

        logger.info("Starting manual login process")

        try:
            # Navigate to Claude.ai
            logger.info("Navigating to claude.ai")
            self.driver.get('https://claude.ai')

            # Wait for page load
            time.sleep(3)

            # Instruct user
            print("\n" + "="*70, file=sys.stderr)
            print("MANUAL LOGIN REQUIRED", file=sys.stderr)
            print("="*70, file=sys.stderr)
            print("Please complete the following steps:", file=sys.stderr)
            print("1. Log in to your Claude.ai account in the browser window", file=sys.stderr)
            print("2. Complete any CAPTCHA or 2FA challenges", file=sys.stderr)
            print("3. Wait until you see your normal Claude.ai interface", file=sys.stderr)
            print("4. Press Enter in this terminal when ready...", file=sys.stderr)
            print("="*70 + "\n", file=sys.stderr)

            input()  # Wait for user confirmation

            # Verify login by checking current URL
            current_url = self.driver.current_url
            if 'claude.ai' in current_url and 'login' not in current_url.lower():
                logger.info("Login successful")
                self.save_session()
                return True
            else:
                logger.warning(f"Login may have failed. Current URL: {current_url}")
                return False

        except Exception as e:
            logger.error(f"Manual login failed: {e}")
            raise

    def save_session(self):
        """Save cookies and session metadata to disk"""
        try:
            cookies = self.driver.get_cookies()
            session_data = {
                'cookies': cookies,
                'timestamp': time.time(),
                'user_agent': self.driver.execute_script('return navigator.userAgent')
            }

            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

            logger.info(f"Session saved to {self.session_file}")

        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def load_session(self):
        """
        Load saved session from disk

        Returns:
            bool: True if valid session exists and is loaded
        """
        if not self.session_file.exists():
            logger.info("No saved session found")
            return False

        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)

            # Check session age (expire after 7 days)
            session_age = time.time() - session_data['timestamp']
            if session_age > 7 * 24 * 3600:
                logger.warning(f"Session expired (age: {session_age/3600:.1f} hours)")
                return False

            logger.info(f"Loaded session from {session_age/3600:.1f} hours ago")
            return True

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    def check_session_valid(self):
        """
        Verify that current session is still authenticated

        Returns:
            bool: True if session is valid (not redirected to login)
        """
        try:
            current_url = self.driver.current_url

            # Check for login redirect
            if 'login' in current_url.lower() or 'auth' in current_url.lower():
                logger.warning("Session invalid: redirected to login")
                return False

            # Check for authentication required elements
            try:
                self.driver.find_element(By.XPATH, "//*[contains(text(), 'log in') or contains(text(), 'Log in')]")
                logger.warning("Session invalid: login prompt found")
                return False
            except:
                pass  # Element not found = good

            logger.info("Session is valid")
            return True

        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False

    def navigate_to_usage_page(self):
        """
        Navigate to claude.ai/settings/usage

        Returns:
            bool: True if navigation successful
        """
        try:
            logger.info("Navigating to usage page")
            self.driver.get('https://claude.ai/settings/usage')

            # Wait for page load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Additional wait for React to render
            time.sleep(3)

            # Verify we're on the right page
            if 'settings/usage' not in self.driver.current_url:
                logger.error(f"Navigation failed. Current URL: {self.driver.current_url}")
                return False

            logger.info("Successfully navigated to usage page")
            return True

        except Exception as e:
            logger.error(f"Failed to navigate to usage page: {e}")
            return False

    def extract_usage_data(self):
        """
        Extract usage metrics from the DOM
        Uses multiple extraction strategies with fallbacks

        Returns:
            dict: Usage data with keys:
                - usage_percent: float (0-100)
                - tokens_used: int
                - tokens_limit: int
                - tokens_remaining: int
                - reset_time: ISO 8601 string
                - last_updated: ISO 8601 string
        """
        logger.info("Extracting usage data from page")

        try:
            # Strategy 1: Execute JavaScript to find usage elements
            data = self.driver.execute_script("""
                // Helper to safely get text content
                function getText(selectors) {
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            const text = el.textContent.trim();
                            if (text) return text;
                        }
                    }
                    return null;
                }

                // Helper to extract numbers from text
                function extractNumber(text) {
                    if (!text) return null;
                    const match = text.match(/[0-9,]+/);
                    return match ? parseInt(match[0].replace(/,/g, '')) : null;
                }

                // Helper to extract percentage
                function extractPercent(text) {
                    if (!text) return null;
                    const match = text.match(/([0-9.]+)%/);
                    return match ? parseFloat(match[1]) : null;
                }

                // Try to find usage information
                // Claude.ai UI may use various class names and structures
                const results = {
                    raw_text: document.body.innerText,
                    html_sample: document.body.innerHTML.substring(0, 5000)
                };

                // Look for common patterns in the text
                const bodyText = document.body.innerText;

                // Pattern 1: "X of Y messages" or "X / Y tokens"
                const usageMatch = bodyText.match(/([0-9,]+)\\s*(?:of|\\/|\\/)\\s*([0-9,]+)/);
                if (usageMatch) {
                    results.tokens_used = parseInt(usageMatch[1].replace(/,/g, ''));
                    results.tokens_limit = parseInt(usageMatch[2].replace(/,/g, ''));
                }

                // Pattern 2: Percentage
                const percentMatch = bodyText.match(/([0-9.]+)%/);
                if (percentMatch) {
                    results.usage_percent = parseFloat(percentMatch[1]);
                }

                // Pattern 3: Reset time - look for "resets in" or similar
                const resetMatch = bodyText.match(/resets?\\s+(?:in\\s+)?([0-9]+)\\s*hours?\\s*(?:and\\s*)?([0-9]+)?\\s*minutes?/i);
                if (resetMatch) {
                    results.reset_hours = parseInt(resetMatch[1]);
                    results.reset_minutes = resetMatch[2] ? parseInt(resetMatch[2]) : 0;
                }

                return results;
            """)

            logger.debug(f"Extracted raw data: {json.dumps(data, indent=2)}")

            # Parse and structure the data
            usage_data = self._parse_extracted_data(data)

            logger.info(f"Successfully extracted usage data: {json.dumps(usage_data, indent=2)}")
            return usage_data

        except Exception as e:
            logger.error(f"Failed to extract usage data: {e}")

            # Fallback: Try basic text extraction
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                logger.debug(f"Page text (first 1000 chars): {body_text[:1000]}")

                # Try to extract from plain text
                return self._parse_plain_text(body_text)

            except Exception as e2:
                logger.error(f"Fallback extraction also failed: {e2}")
                raise

    def _parse_extracted_data(self, data):
        """
        Parse the raw extracted data into structured format

        Args:
            data: Dictionary from JavaScript extraction

        Returns:
            dict: Structured usage data
        """
        # Calculate usage percentage
        usage_percent = data.get('usage_percent')
        if usage_percent is None and 'tokens_used' in data and 'tokens_limit' in data:
            usage_percent = (data['tokens_used'] / data['tokens_limit']) * 100

        # Calculate reset time
        reset_time = None
        if 'reset_hours' in data:
            hours = data['reset_hours']
            minutes = data.get('reset_minutes', 0)
            reset_time = (datetime.utcnow() + timedelta(hours=hours, minutes=minutes)).isoformat() + 'Z'

        # Calculate remaining tokens
        tokens_remaining = None
        if 'tokens_used' in data and 'tokens_limit' in data:
            tokens_remaining = data['tokens_limit'] - data['tokens_used']

        return {
            'usage_percent': round(usage_percent, 1) if usage_percent else 0,
            'tokens_used': data.get('tokens_used', 0),
            'tokens_limit': data.get('tokens_limit', 88000),  # Default for Max plan
            'tokens_remaining': tokens_remaining if tokens_remaining else 88000,
            'reset_time': reset_time,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'status': 'success'
        }

    def _parse_plain_text(self, text):
        """
        Fallback parser for plain text extraction

        Args:
            text: Page body text

        Returns:
            dict: Best-effort usage data
        """
        logger.info("Using fallback plain text parser")

        # Try to extract tokens used/limit
        usage_match = re.search(r'([0-9,]+)\s*(?:of|/)\s*([0-9,]+)', text)
        tokens_used = int(usage_match.group(1).replace(',', '')) if usage_match else 0
        tokens_limit = int(usage_match.group(2).replace(',', '')) if usage_match else 88000

        # Calculate percentage
        usage_percent = (tokens_used / tokens_limit) * 100 if tokens_limit > 0 else 0

        # Try to extract reset time
        reset_match = re.search(r'resets?\s+(?:in\s+)?([0-9]+)\s*hours?\s*(?:and\s*)?([0-9]+)?\s*minutes?', text, re.IGNORECASE)
        reset_time = None
        if reset_match:
            hours = int(reset_match.group(1))
            minutes = int(reset_match.group(2)) if reset_match.group(2) else 0
            reset_time = (datetime.utcnow() + timedelta(hours=hours, minutes=minutes)).isoformat() + 'Z'

        return {
            'usage_percent': round(usage_percent, 1),
            'tokens_used': tokens_used,
            'tokens_limit': tokens_limit,
            'tokens_remaining': tokens_limit - tokens_used,
            'reset_time': reset_time,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'status': 'partial',  # Indicate this was fallback extraction
            'warning': 'Used fallback text extraction'
        }

    def poll_usage(self):
        """
        Main polling function: navigate to page and extract usage data

        Returns:
            dict: Usage data or error information
        """
        if not self.driver:
            self.create_driver()

            # Check if we have a valid session
            if not self.load_session():
                logger.error("No valid session. Manual login required.")
                return {
                    'status': 'error',
                    'error': 'session_required',
                    'message': 'No saved session found. Please run manual_login first.'
                }

        try:
            # Navigate to usage page
            if not self.navigate_to_usage_page():
                return {
                    'status': 'error',
                    'error': 'navigation_failed',
                    'message': 'Failed to navigate to usage page'
                }

            # Check if session is still valid
            if not self.check_session_valid():
                return {
                    'status': 'error',
                    'error': 'session_expired',
                    'message': 'Session expired. Manual re-login required.'
                }

            # Extract usage data
            usage_data = self.extract_usage_data()
            return usage_data

        except Exception as e:
            logger.error(f"Poll failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': 'extraction_failed',
                'message': str(e)
            }

    def close(self):
        """Clean up: close browser and save session"""
        if self.driver:
            try:
                logger.info("Closing browser")
                self.driver.quit()
                self.driver = None
            except Exception as e:
                logger.error(f"Error closing browser: {e}")


def main():
    """
    Main entry point for CLI usage
    Outputs JSON to stdout for consumption by parent process
    Logs to stderr for debugging
    """
    import argparse

    parser = argparse.ArgumentParser(description='Scrape Claude.ai usage data')
    parser.add_argument('--login', action='store_true', help='Perform manual login')
    parser.add_argument('--profile-dir', default='./chrome-profile', help='Browser profile directory')
    args = parser.parse_args()

    scraper = ClaudeUsageScraper(profile_dir=args.profile_dir)

    try:
        if args.login:
            # Manual login mode
            logger.info("Starting manual login")
            success = scraper.manual_login()

            if success:
                result = {
                    'status': 'success',
                    'message': 'Login successful. Session saved.'
                }
            else:
                result = {
                    'status': 'error',
                    'error': 'login_failed',
                    'message': 'Login appears to have failed. Please try again.'
                }
        else:
            # Normal polling mode
            logger.info("Starting usage poll")
            result = scraper.poll_usage()

        # Output JSON to stdout (Rust will read this)
        print(json.dumps(result, indent=2))

        # Exit with appropriate code
        sys.exit(0 if result.get('status') == 'success' else 1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

        error_result = {
            'status': 'error',
            'error': 'fatal',
            'message': str(e)
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

    finally:
        scraper.close()


if __name__ == '__main__':
    main()
