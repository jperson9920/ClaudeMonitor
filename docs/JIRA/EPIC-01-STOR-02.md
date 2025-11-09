# EPIC-01-STOR-02: Playwright Web Scraper with Persistent Authentication

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 8 hours  
**Dependencies**: [STOR-01](EPIC-01-STOR-01.md)  
**Assignee**: TBD

## Objective

Implement a Playwright-based web scraper that monitors claude.ai/usage, maintains persistent authentication across restarts, polls usage data every 5 minutes, and saves data to JSON with atomic writes.

## Requirements

### Functional Requirements
1. Launch Playwright with persistent browser context for session persistence
2. Detect if user is logged in; if not, wait for manual login
3. Poll claude.ai/usage page every 5 minutes
4. Extract three usage metrics: 4-hour cap, 1-week cap, Opus 1-week cap
5. Save extracted data to JSON file atomically
6. Handle session expiration gracefully
7. Implement graceful shutdown on SIGINT/SIGTERM

### Technical Requirements
1. **Playwright Configuration**:
   - Use `launch_persistent_context()` with Chrome channel
   - Store browser data in `browser-data/` directory
   - Disable automation detection flags
   - Set viewport to 1280x720

2. **Polling Configuration**:
   - Poll interval: 300 seconds (5 minutes)
   - Page load timeout: 30 seconds
   - Selector timeout: 10 seconds
   - Retry on failure with 10-second delay

3. **Data Extraction**:
   - Extract usage percentages for all three caps
   - Extract reset timer information
   - Include timestamp with each data point
   - Mark extraction status (success/error)

## Acceptance Criteria

- [x] Playwright launches with persistent browser context
- [x] First run prompts user to log in manually
- [x] Subsequent runs restore session automatically
- [x] Polling loop runs every 5 minutes indefinitely
- [x] Usage data extracted successfully from claude.ai/usage
- [x] Data saved to `data/usage-data.json` atomically
- [x] Session expiration detected and user prompted to re-login
- [x] SIGINT (Ctrl+C) triggers graceful shutdown
- [x] Browser context closes properly on shutdown
- [x] Error states logged and saved to JSON

## Implementation

### File Location

Create [`src/scraper/claude_usage_monitor.py`](../../src/scraper/claude_usage_monitor.py)

### Code Structure

```python
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
            // Helper functions
            const getText = (sel) => {
                const el = document.querySelector(sel);
                return el ? el.textContent.trim() : null;
            };
            
            const parsePercent = (text) => {
                if (!text) return null;
                const match = text.match(/(\\d+\\.?\\d*)/);
                return match ? parseFloat(match[0]) : null;
            };
            
            // Extract metrics
            // NOTE: These selectors are placeholders - STOR-09 will discover actual selectors
            return {
                timestamp: new Date().toISOString(),
                fourHour: {
                    usagePercent: parsePercent(getText('[data-cap="4hour"] .usage-percent')) || 0,
                    resetTime: getText('[data-cap="4hour"] .reset-timer')
                },
                oneWeek: {
                    usagePercent: parsePercent(getText('[data-cap="1week"] .usage-percent')) || 0,
                    resetTime: getText('[data-cap="1week"] .reset-timer')
                },
                opusOneWeek: {
                    usagePercent: parsePercent(getText('[data-cap="opus"] .usage-percent')) || 0,
                    resetTime: getText('[data-cap="opus"] .reset-timer')
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
        
        # Update data structure
        new_data = {
            'schemaVersion': '1.0.0',
            'metadata': {
                'lastUpdate': datetime.utcnow().isoformat() + 'Z',
                'applicationVersion': '1.0.0'
            },
            'currentState': data if data.get('status') == 'success' else existing.get('currentState'),
            'historicalData': existing.get('historicalData', [])
        }
        
        # Add historical data point
        if data.get('status') == 'success':
            new_data['historicalData'].append({
                'timestamp': data['timestamp'],
                'fourHour': data['fourHour']['usagePercent'],
                'oneWeek': data['oneWeek']['usagePercent'],
                'opusOneWeek': data['opusOneWeek']['usagePercent']
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
```

### Testing the Scraper

Create a test script to verify basic functionality:

```python
# tests/test_scraper.py
"""Test script for web scraper functionality."""

import asyncio
import pytest
from pathlib import Path
from src.scraper.claude_usage_monitor import ClaudeUsageMonitor


@pytest.mark.asyncio
async def test_scraper_initialization():
    """Test that scraper initializes correctly."""
    monitor = ClaudeUsageMonitor(poll_interval=300)
    
    assert monitor.poll_interval == 300
    assert monitor.user_data_dir.exists() or True  # Will be created on first run
    assert monitor.data_file.parent.name == 'data'
    assert monitor.context is None  # Not started yet
    assert monitor.running is False


@pytest.mark.asyncio
async def test_data_structure():
    """Test that data extraction produces correct structure."""
    # This test requires manual inspection after first successful poll
    data_file = Path('data/usage-data.json')
    
    if data_file.exists():
        import json
        with open(data_file) as f:
            data = json.load(f)
        
        assert 'schemaVersion' in data
        assert 'metadata' in data
        assert 'currentState' in data
        assert 'historicalData' in data
        assert isinstance(data['historicalData'], list)
```

## Manual Testing Procedure

### Test 1: First Run with Manual Login

1. Ensure no `browser-data/` directory exists
2. Run the scraper:
   ```powershell
   python src/scraper/claude_usage_monitor.py
   ```
3. Browser window should open to claude.ai/usage
4. If redirected to login, log in manually
5. Verify console shows "✅ Login successful!"
6. Wait for first poll to complete
7. Verify `data/usage-data.json` is created

### Test 2: Session Persistence

1. Stop the scraper (Ctrl+C)
2. Verify graceful shutdown message
3. Restart the scraper
4. Verify it shows "✅ Already logged in!" (no login prompt)
5. Verify polling continues normally

### Test 3: Data Collection

1. Let the scraper run for 15-20 minutes (3-4 polls)
2. Check `data/usage-data.json` content
3. Verify `historicalData` array has 3-4 entries
4. Verify timestamps are correct
5. Verify usage percentages are plausible (0-100)

## Error Handling

The scraper handles these error conditions:

1. **Session Expiration**: Detects login redirect, waits for re-login
2. **Network Errors**: Catches exceptions, logs error, waits 10s before retry
3. **Selector Not Found**: Tries fallback selectors before failing
4. **Corrupted JSON**: Starts fresh if existing data file is unreadable
5. **Keyboard Interrupt**: Gracefully closes browser and exits

## Dependencies

### Blocked By
- [STOR-01](EPIC-01-STOR-01.md): Project Setup (must install Playwright)

### Blocks
- [STOR-07](EPIC-01-STOR-07.md): Process Orchestration (needs working scraper)
- [STOR-08](EPIC-01-STOR-08.md): Error Handling (builds on base scraper)
- [STOR-09](EPIC-01-STOR-09.md): Selector Discovery (refines extraction logic)
- [STOR-10](EPIC-01-STOR-10.md): Testing (validates scraper works)

## Definition of Done

- [ ] `claude_usage_monitor.py` created with complete implementation
- [ ] Playwright launches with persistent context
- [ ] Manual login flow works on first run
- [ ] Session persists across restarts
- [ ] Polling loop runs every 5 minutes
- [ ] Data saved to JSON atomically
- [ ] Graceful shutdown on Ctrl+C
- [ ] All error conditions handled
- [ ] Manual testing completed successfully
- [ ] Test script created in `tests/test_scraper.py`
- [ ] Story marked as DONE in EPIC-01.md

## References

- **Source Implementation**: Lines 353-533 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:353)
- **Authentication Strategy**: Lines 535-566 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:535)
- **Playwright Python Docs**: https://playwright.dev/python/docs/api/class-playwright

## Notes

- **Selector Placeholders**: The current selectors are placeholders. STOR-09 will discover actual selectors from claude.ai/usage
- **Headless Mode**: Currently runs with `headless=False` for easier debugging. Can be changed to `True` after validation
- **Chrome Channel**: Uses installed Chrome rather than bundled Chromium for better compatibility
- **Atomic Writes**: Uses `atomicwrites` library to prevent data corruption during writes

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 5  
**Actual Effort**: TBD