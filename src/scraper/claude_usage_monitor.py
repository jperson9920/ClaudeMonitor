# src/scraper/claude_usage_monitor.py
"""
Claude Usage Monitor - Web Scraper Component

Polls claude.ai/usage every 5 minutes and extracts usage data.
Uses Playwright with persistent browser context for session management.

Reference: compass_artifact document lines 353-533
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, BrowserContext, Page
from atomicwrites import atomic_write


class ClaudeUsageMonitor:
    """Main scraper class for monitoring Claude usage data."""

    def __init__(self, poll_interval: int = 300):
        """
        Initialize the Claude Usage Monitor.

        Args:
            poll_interval: Polling interval in seconds (default 300 = 5 minutes)
        """
        self.poll_interval = poll_interval
        self.user_data_dir = Path(__file__).parent.parent.parent / 'browser-data'
        self.data_file = Path(__file__).parent.parent.parent / 'data' / 'usage-data.json'
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.running = False

        # Migrate any legacy on-disk data to the new schema so tests and consumers
        # that read the file find the expected top-level keys.
        self._migrate_existing_file()

    def _migrate_existing_file(self) -> None:
        """
        Ensure existing on-disk data conforms to the expected schema.
        If the file exists but lacks top-level keys (schemaVersion, metadata,
        currentState, historicalData), transform it into the canonical shape.
        """
        try:
            if not self.data_file.exists():
                return

            with open(self.data_file, 'r') as f:
                raw = json.load(f)

            # If already has schemaVersion, nothing to do
            if isinstance(raw, dict) and 'schemaVersion' in raw:
                return

            # Legacy format detected — attempt to normalize
            normalized = {
                'schemaVersion': '1.0.0',
                'metadata': {
                    'lastUpdate': datetime.utcnow().isoformat() + 'Z',
                    'applicationVersion': '1.0.0'
                },
                # If legacy used 'historicalData' as top-level, preserve it
                'currentState': raw.get('currentState') if isinstance(raw, dict) else None,
                'historicalData': raw.get('historicalData', []) if isinstance(raw, dict) else []
            }

            # If legacy file was a list or other structure, attempt best-effort conversion
            if isinstance(raw, list):
                normalized['historicalData'] = raw

            # Overwrite with normalized structure atomically
            with atomic_write(str(self.data_file), overwrite=True) as f:
                json.dump(normalized, f, indent=2)

            print(f'🔧 Migrated legacy data file to canonical schema: {self.data_file}')

        except Exception as e:
            print(f'⚠️  Failed to migrate existing data file: {e}')

    async def start(self) -> None:
        """Start the monitoring system."""
        async with async_playwright() as p:
            # Launch persistent context (maintains authentication)
            print(f"📂 Using browser data directory: {self.user_data_dir}")
            self.context = await p.chromium.launch_persistent_context(
                str(self.user_data_dir),
                headless=False,
                channel='chrome',
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ],
                viewport={'width': 1280, 'height': 720}
            )

            # Check authentication
            self.page = await self.context.new_page()
            print("🔍 Checking authentication status...")
            await self.page.goto('https://claude.ai/usage',
                               wait_until='networkidle',
                               timeout=30000)

            if '/login' in self.page.url:
                print('⚠️  Please log in manually in the browser window...')
                print('⏳ Waiting for you to complete login (5 minute timeout)...')
                await self.page.wait_for_url('**/usage', timeout=300000)
                print('✅ Login successful!')
            else:
                print('✅ Already logged in!')

            # Start polling loop
            self.running = True
            await self.poll_loop()

    async def poll_loop(self) -> None:
        """Main polling loop."""
        print(f"🔄 Starting poll loop (interval: {self.poll_interval}s)")

        while self.running:
            try:
                await self.poll()
                await asyncio.sleep(self.poll_interval)
            except KeyboardInterrupt:
                print('\n🛑 Received shutdown signal...')
                self.running = False
                break
            except Exception as e:
                print(f'❌ Error in poll loop: {e}')
                await asyncio.sleep(10)  # Wait before retry

    async def poll(self) -> None:
        """Poll usage data from claude.ai/usage."""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        print(f'[{timestamp}] 📊 Polling usage data...')

        try:
            # Navigate to usage page
            await self.page.goto('https://claude.ai/usage',
                               wait_until='networkidle',
                               timeout=30000)

            # Check if session expired
            if '/login' in self.page.url:
                print('⚠️  Session expired. Please log in again.')
                print('⏳ Waiting for login...')
                await self.page.wait_for_url('**/usage', timeout=300000)
                print('✅ Login successful!')
                return  # Skip this poll, next one will collect data

            # Wait for metrics to load
            # Try primary selector, fall back to generic if needed
            try:
                await self.page.wait_for_selector('[data-testid="usage-metric"]',
                                                timeout=10000)
            except:
                print('⚠️  Primary selector not found, trying fallback...')
                await self.page.wait_for_selector('.usage-metric, [class*="usage"]',
                                                timeout=10000)

            # Extract data
            usage_data = await self.extract_usage_data()

            # Save to file
            await self.save_data(usage_data)

            print(f'✅ Poll successful')
            print(f'   4-Hour: {usage_data["fourHour"]["usagePercent"]:.1f}%')
            print(f'   1-Week: {usage_data["oneWeek"]["usagePercent"]:.1f}%')
            print(f'   Opus 1-Week: {usage_data["opusOneWeek"]["usagePercent"]:.1f}%')

        except Exception as e:
            print(f'❌ Poll failed: {e}')

            # Save error state
            await self.save_data({
                'timestamp': timestamp,
                'error': str(e),
                'status': 'error'
            })

    async def extract_usage_data(self) -> Dict[str, Any]:
        """
        Extract usage data from the page.

        Returns:
            Dictionary containing usage data for all three caps
        """
        return await self.page.evaluate('''() => {
            // Helper: try multiple selectors in priority order
            const getTextBySelectors = (selectors) => {
                for (const selector of selectors) {
                    try {
                        const el = document.querySelector(selector);
                        if (el) return el.textContent.trim();
                    } catch (e) {}
                }
                return null;
            };

            const parsePercent = (text) => {
                if (!text) return 0;
                const match = text.match(/(\\d+\\.?\\d*)/);
                return match ? parseFloat(match[0]) : 0;
            };

            // 4-Hour Cap selectors (in priority order)
            const fourHourPercentSelectors = [
                '[data-testid="usage-4hour-percent"]',
                '.usage-metric[data-period="4h"] .percentage',
                '[data-cap="4hour"] .usage-percent'
            ];

            const fourHourResetSelectors = [
                '[data-testid="usage-4hour-reset"]',
                '.usage-metric[data-period="4h"] .reset-time',
                '[data-cap="4hour"] .reset-timer'
            ];

            // 1-Week Cap selectors
            const oneWeekPercentSelectors = [
                '[data-testid="usage-1week-percent"]',
                '.usage-metric[data-period="1w"] .percentage',
                '[data-cap="1week"] .usage-percent'
            ];

            const oneWeekResetSelectors = [
                '[data-testid="usage-1week-reset"]',
                '.usage-metric[data-period="1w"] .reset-time',
                '[data-cap="1week"] .reset-timer'
            ];

            // Opus 1-Week Cap selectors
            const opusPercentSelectors = [
                '[data-testid="usage-opus-percent"]',
                '.usage-metric[data-model="opus"] .percentage',
                '[data-cap="opus"] .usage-percent'
            ];

            const opusResetSelectors = [
                '[data-testid="usage-opus-reset"]',
                '.usage-metric[data-model="opus"] .reset-time',
                '[data-cap="opus"] .reset-timer'
            ];

            return {
                timestamp: new Date().toISOString(),
                fourHour: {
                    usagePercent: parsePercent(getTextBySelectors(fourHourPercentSelectors)),
                    resetTime: getTextBySelectors(fourHourResetSelectors)
                },
                oneWeek: {
                    usagePercent: parsePercent(getTextBySelectors(oneWeekPercentSelectors)),
                    resetTime: getTextBySelectors(oneWeekResetSelectors)
                },
                opusOneWeek: {
                    usagePercent: parsePercent(getTextBySelectors(opusPercentSelectors)),
                    resetTime: getTextBySelectors(opusResetSelectors)
                },
                status: 'success'
            };
        }''')

    async def save_data(self, data: Dict[str, Any]) -> None:
        """
        Save usage data to JSON file atomically.

        Args:
            data: Usage data dictionary
        """
        # Ensure data directory exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        # Read existing data
        existing = {'historicalData': []}
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    existing = json.load(f)
            except Exception as e:
                print(f'⚠️  Failed to read existing data: {e}')

        # Build canonical data structure
        new_data = {
            'schemaVersion': '1.0.0',
            'metadata': {
                'lastUpdate': datetime.utcnow().isoformat() + 'Z',
                'applicationVersion': '1.0.0'
            },
            'currentState': data if data.get('status') == 'success' else existing.get('currentState'),
            'historicalData': existing.get('historicalData', [])
        }

        # Add historical data point when poll succeeded
        if data.get('status') == 'success':
            new_data['historicalData'].append({
                'timestamp': data.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                'fourHour': data.get('fourHour', {}).get('usagePercent', 0),
                'oneWeek': data.get('oneWeek', {}).get('usagePercent', 0),
                'opusOneWeek': data.get('opusOneWeek', {}).get('usagePercent', 0)
            })

            # Keep only last week of data (2016 points = 7 days * 24 hours * 12 intervals)
            if len(new_data['historicalData']) > 2016:
                new_data['historicalData'] = new_data['historicalData'][-2016:]

        # Atomic write
        with atomic_write(str(self.data_file), overwrite=True) as f:
            json.dump(new_data, f, indent=2)

    async def stop(self) -> None:
        """Stop monitoring and clean up resources."""
        self.running = False
        if self.context:
            await self.context.close()
        print('🛑 Monitoring stopped')


async def main():
    """Main entry point."""
    monitor = ClaudeUsageMonitor(poll_interval=300)

    try:
        await monitor.start()
    except KeyboardInterrupt:
        print('\n🛑 Shutting down...')
        await monitor.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n✅ Shutdown complete')
        sys.exit(0)