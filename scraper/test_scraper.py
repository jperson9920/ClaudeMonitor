#!/usr/bin/env python3
"""
Unit tests for Claude Usage Scraper
"""

import unittest
import json
import time
from pathlib import Path
from claude_scraper import ClaudeUsageScraper


class TestClaudeUsageScraper(unittest.TestCase):
    """Test cases for ClaudeUsageScraper"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_profile_dir = './test-chrome-profile'
        self.scraper = ClaudeUsageScraper(profile_dir=self.test_profile_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up test profile directory
        import shutil
        if Path(self.test_profile_dir).exists():
            shutil.rmtree(self.test_profile_dir)

    def test_initialization(self):
        """Test scraper initialization"""
        self.assertIsNotNone(self.scraper)
        self.assertTrue(Path(self.test_profile_dir).exists())
        self.assertIsNone(self.scraper.driver)

    def test_parse_extracted_data_full(self):
        """Test parsing with complete data"""
        raw_data = {
            'tokens_used': 45000,
            'tokens_limit': 88000,
            'reset_hours': 5,
            'reset_minutes': 30
        }

        result = self.scraper._parse_extracted_data(raw_data)

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['tokens_used'], 45000)
        self.assertEqual(result['tokens_limit'], 88000)
        self.assertEqual(result['tokens_remaining'], 43000)
        self.assertAlmostEqual(result['usage_percent'], 51.1, places=1)
        self.assertIsNotNone(result['reset_time'])
        self.assertIsNotNone(result['last_updated'])

    def test_parse_extracted_data_partial(self):
        """Test parsing with partial data"""
        raw_data = {
            'usage_percent': 75.5
        }

        result = self.scraper._parse_extracted_data(raw_data)

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['usage_percent'], 75.5)
        self.assertEqual(result['tokens_limit'], 88000)  # Default
        self.assertIsNotNone(result['last_updated'])

    def test_parse_plain_text_with_usage(self):
        """Test plain text parsing with usage data"""
        sample_text = """
        Claude Usage
        You have used 52,341 of 88,000 messages this month.
        Your usage resets in 3 hours and 45 minutes.
        """

        result = self.scraper._parse_plain_text(sample_text)

        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['tokens_used'], 52341)
        self.assertEqual(result['tokens_limit'], 88000)
        self.assertEqual(result['tokens_remaining'], 35659)
        self.assertAlmostEqual(result['usage_percent'], 59.5, places=1)
        self.assertIsNotNone(result['reset_time'])
        self.assertEqual(result['warning'], 'Used fallback text extraction')

    def test_parse_plain_text_no_data(self):
        """Test plain text parsing with no usage data"""
        sample_text = "Welcome to Claude.ai"

        result = self.scraper._parse_plain_text(sample_text)

        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['tokens_used'], 0)
        self.assertEqual(result['tokens_limit'], 88000)  # Default
        self.assertIsNone(result['reset_time'])

    def test_session_file_location(self):
        """Test session file path"""
        expected_path = Path(self.test_profile_dir).resolve() / 'session.json'
        self.assertEqual(self.scraper.session_file, expected_path)

    def test_load_session_no_file(self):
        """Test loading session when no file exists"""
        result = self.scraper.load_session()
        self.assertFalse(result)

    def test_save_and_load_session(self):
        """Test saving and loading session (requires driver)"""
        # This test would require a real driver, so we'll skip it in unit tests
        # It should be tested manually or with integration tests
        self.skipTest("Requires browser driver - test manually")


class TestDataExtraction(unittest.TestCase):
    """Test data extraction patterns"""

    def test_usage_pattern_matching(self):
        """Test various usage pattern formats"""
        import re

        patterns = [
            ("45,000 of 88,000", (45000, 88000)),
            ("45000 / 88000", (45000, 88000)),
            ("12,345 of 88,000 messages", (12345, 88000)),
            ("0 of 88,000", (0, 88000)),
        ]

        for text, expected in patterns:
            match = re.search(r'([0-9,]+)\s*(?:of|/)\s*([0-9,]+)', text)
            self.assertIsNotNone(match, f"Failed to match: {text}")
            used = int(match.group(1).replace(',', ''))
            limit = int(match.group(2).replace(',', ''))
            self.assertEqual((used, limit), expected)

    def test_reset_time_pattern_matching(self):
        """Test reset time pattern formats"""
        import re

        patterns = [
            ("resets in 5 hours", (5, 0)),
            ("Resets in 3 hours and 30 minutes", (3, 30)),
            ("Reset in 12 hours 45 minutes", (12, 45)),
            ("resets 1 hour", (1, 0)),
        ]

        for text, expected in patterns:
            match = re.search(
                r'resets?\s+(?:in\s+)?([0-9]+)\s*hours?\s*(?:and\s*)?([0-9]+)?\s*minutes?',
                text,
                re.IGNORECASE
            )
            self.assertIsNotNone(match, f"Failed to match: {text}")
            hours = int(match.group(1))
            minutes = int(match.group(2)) if match.group(2) else 0
            self.assertEqual((hours, minutes), expected)


def run_integration_test():
    """
    Integration test - requires manual interaction
    Run this separately: python test_scraper.py integration
    """
    print("\n" + "="*70)
    print("INTEGRATION TEST - Manual Login Flow")
    print("="*70)
    print("This test will open a browser for manual login.")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    print("="*70 + "\n")

    try:
        input()
    except KeyboardInterrupt:
        print("\nTest cancelled")
        return

    scraper = ClaudeUsageScraper(profile_dir='./test-integration-profile')

    try:
        print("\n1. Testing manual login...")
        success = scraper.manual_login()
        if success:
            print("✓ Manual login successful")
        else:
            print("✗ Manual login failed")
            return

        print("\n2. Testing automated polling...")
        result = scraper.poll_usage()
        if result.get('status') == 'success':
            print("✓ Polling successful")
            print(f"\nUsage Data:")
            print(json.dumps(result, indent=2))
        else:
            print("✗ Polling failed")
            print(f"Error: {result.get('message')}")

    finally:
        scraper.close()
        print("\n✓ Integration test complete")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'integration':
        run_integration_test()
    else:
        # Run unit tests
        unittest.main()
