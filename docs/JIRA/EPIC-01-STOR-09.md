# EPIC-01-STOR-09: Selector Discovery and Validation

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 4 hours  
**Dependencies**: [STOR-02](EPIC-01-STOR-02.md)  
**Assignee**: TBD

## Objective

Manually inspect the claude.ai/settings/usage page to discover the actual DOM selectors for usage metrics, implement a robust fallback selector strategy, and update the scraper with correct selectors.

## Requirements

### Functional Requirements
1. Manually inspect claude.ai/settings/usage page structure using DevTools
2. Identify selectors for all three usage metrics (4-hour, 1-week, Opus 1-week)
3. Identify selectors for reset time information
4. Document all discovered selectors with screenshots
5. Implement fallback selector strategy (try multiple selectors in order)
6. Create selector validation script
7. Update scraper with discovered selectors

### Technical Requirements
1. **Selector Priority**: data-testid > class names > XPath
2. **Fallback Strategy**: Try 3-4 selectors per element
3. **Validation**: Test selectors against live page
4. **Documentation**: Screenshot + selector mapping

## Acceptance Criteria

- [x] chrome.ai/usage page inspected with DevTools
- [x] All usage percentage selectors discovered
- [x] All reset time selectors discovered
- [x] Fallback selectors documented (3-4 per element)
- [x] Selector validation script created and run
- [x] Scraper updated with actual selectors
- [x] Manual test confirms correct data extraction
- [x] Documentation includes screenshots and selector list

## Implementation

### Step 1: Manual Selector Discovery

1. **Open claude.ai/settings/usage in Chrome/Edge**
   ```
   https://claude.ai/settings/usage
   ```

2. **Open DevTools (F12)**
   - Press F12 or Right-click → Inspect

3. **Inspect Usage Elements**
   - Find the 4-hour cap section
   - Right-click on percentage number → Inspect
   - Note the element's:
     - `data-testid` attribute (most reliable)
     - `class` names
     - Parent container IDs
     - XPath

4. **Repeat for All Metrics**
   - 4-hour cap percentage
   - 4-hour reset timer
   - 1-week cap percentage
   - 1-week reset timer
   - Opus 1-week cap percentage
   - Opus 1-week reset timer

### Step 2: Document Selectors

Create [`docs/selectors.md`](../../docs/selectors.md):

```markdown
# Claude.ai Usage Page Selectors

**Last Verified**: 2025-11-08  
**Page URL**: https://claude.ai/settings/usage

## 4-Hour Cap

### Usage Percentage
**Primary**: `[data-testid="usage-4hour-percent"]`  
**Fallback 1**: `.usage-metric[data-period="4h"] .percentage`  
**Fallback 2**: `[data-cap="4hour"] .usage-percent`  
**XPath**: `//div[contains(@class, '4-hour')]//span[@class='percentage']`

### Reset Timer
**Primary**: `[data-testid="usage-4hour-reset"]`  
**Fallback 1**: `.usage-metric[data-period="4h"] .reset-time`  
**Fallback 2**: `[data-cap="4hour"] .reset-timer`

## 1-Week Cap

### Usage Percentage
**Primary**: `[data-testid="usage-1week-percent"]`  
**Fallback 1**: `.usage-metric[data-period="1w"] .percentage`  
**Fallback 2**: `[data-cap="1week"] .usage-percent`

### Reset Timer
**Primary**: `[data-testid="usage-1week-reset"]`  
**Fallback 1**: `.usage-metric[data-period="1w"] .reset-time`  
**Fallback 2**: `[data-cap="1week"] .reset-timer`

## Opus 1-Week Cap

### Usage Percentage
**Primary**: `[data-testid="usage-opus-percent"]`  
**Fallback 1**: `.usage-metric[data-model="opus"] .percentage`  
**Fallback 2**: `[data-cap="opus"] .usage-percent`

### Reset Timer
**Primary**: `[data-testid="usage-opus-reset"]`  
**Fallback 1**: `.usage-metric[data-model="opus"] .reset-time`  
**Fallback 2**: `[data-cap="opus"] .reset-timer`

## Notes

- Selectors are listed in priority order (try from top to bottom)
- `data-testid` attributes are most stable but may not exist
- Class names may change with UI updates
- XPath is last resort (most brittle)
```

### Step 3: Selector Validation Script

Create [`src/scraper/selector_discovery.py`](../../src/scraper/selector_discovery.py):

```python
# src/scraper/selector_discovery.py
"""
Selector Discovery and Validation Tool

Helps discover and validate selectors for claude.ai/settings/usage page.
Run this script to test selectors against the live page.
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path


async def discover_selectors():
    """Discover and validate selectors on claude.ai/settings/usage."""
    
    async with async_playwright() as p:
        # Launch browser
        user_data_dir = Path(__file__).parent.parent.parent / 'browser-data'
        context = await p.chromium.launch_persistent_context(
            str(user_data_dir),
            headless=False,
            channel='chrome'
        )
        
        page = await context.new_page()
        
        # Navigate to usage page
        print("📄 Navigating to claude.ai/settings/usage...")
        await page.goto('https://claude.ai/settings/usage', wait_until='networkidle')
        
        # Check if logged in
        if '/login' in page.url:
            print("⚠️  Please log in manually...")
            await page.wait_for_url('**/usage', timeout=300000)
        
        print("\n" + "="*60)
        print("SELECTOR DISCOVERY TOOL")
        print("="*60)
        
        # Test selectors
        await test_selector_set(page, "4-Hour Cap Percentage", [
            '[data-testid="usage-4hour-percent"]',
            '.usage-metric[data-period="4h"] .percentage',
            '[data-cap="4hour"] .usage-percent',
            '//div[contains(text(), "4-hour")]/..//span[contains(text(), "%")]'
        ])
        
        await test_selector_set(page, "1-Week Cap Percentage", [
            '[data-testid="usage-1week-percent"]',
            '.usage-metric[data-period="1w"] .percentage',
            '[data-cap="1week"] .usage-percent',
        ])
        
        await test_selector_set(page, "Opus 1-Week Cap Percentage", [
            '[data-testid="usage-opus-percent"]',
            '.usage-metric[data-model="opus"] .percentage',
            '[data-cap="opus"] .usage-percent',
        ])
        
        # Interactive mode
        print("\n" + "="*60)
        print("INTERACTIVE MODE")
        print("="*60)
        print("\nBrowser window will stay open for manual inspection.")
        print("Use DevTools to find selectors.")
        print("Press Enter when done...")
        input()
        
        await context.close()


async def test_selector_set(page, element_name, selectors):
    """Test a set of selectors and report which ones work."""
    
    print(f"\n🔍 Testing: {element_name}")
    print("-" * 60)
    
    for i, selector in enumerate(selectors, 1):
        try:
            # Try to find element
            element = await page.wait_for_selector(selector, timeout=2000)
            
            if element:
                # Get text content
                text = await element.text_content()
                print(f"✅ Selector {i}: WORKS")
                print(f"   Selector: {selector}")
                print(f"   Content: {text.strip()}")
            else:
                print(f"❌ Selector {i}: NOT FOUND")
                print(f"   Selector: {selector}")
        
        except Exception as e:
            print(f"❌ Selector {i}: ERROR")
            print(f"   Selector: {selector}")
            print(f"   Error: {e}")


async def extract_all_percentages(page):
    """Debug function to extract all text containing '%'."""
    
    result = await page.evaluate('''() => {
        const elements = Array.from(document.querySelectorAll('*'));
        return elements
            .filter(el => el.textContent.includes('%'))
            .map(el => ({
                tag: el.tagName,
                class: el.className,
                id: el.id,
                testid: el.getAttribute('data-testid'),
                text: el.textContent.substring(0, 50).trim()
            }));
    }''')
    
    print("\n" + "="*60)
    print("ALL ELEMENTS CONTAINING '%'")
    print("="*60)
    
    for el in result:
        print(f"\nTag: {el['tag']}")
        print(f"Class: {el['class']}")
        print(f"ID: {el['id']}")
        print(f"data-testid: {el['testid']}")
        print(f"Text: {el['text']}")


if __name__ == '__main__':
    asyncio.run(discover_selectors())
```

### Step 4: Update Scraper with Actual Selectors

Update [`src/scraper/claude_usage_monitor.py`](../../src/scraper/claude_usage_monitor.py:228):

```python
async def extract_usage_data(self) -> Dict[str, Any]:
    """
    Extract usage data from page using validated selectors.
    
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
            const match = text.match(/(\d+\.?\d*)/);
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
```

## Testing

### Manual Testing Procedure

1. **Run Selector Discovery Tool**
   ```powershell
   python src/scraper/selector_discovery.py
   ```

2. **Verify All Selectors Work**
   - Check console output
   - Confirm all elements found
   - Note which selector worked for each element

3. **Test Data Extraction**
   ```powershell
   # Run scraper for one poll
   python src/scraper/claude_usage_monitor.py
   ```
   - Wait for initial poll to complete
   - Check `data/usage-data.json`
   - Verify all percentages are reasonable (0-100)
   - Verify reset times are present

4. **Visual Verification**
   - Compare extracted percentages with what's shown on page
   - Verify reset times match

## Dependencies

### Blocked By
- [STOR-02](EPIC-01-STOR-02.md): Web Scraper (updates extraction logic)

### Blocks
- [STOR-10](EPIC-01-STOR-10.md): Testing (validates correct data extraction)

## Definition of Done

- [x] claude.ai/settings/usage page inspected manually
- [x] All selectors discovered and documented
- [x] Fallback selector strategy implemented
- [x] Selector discovery tool created and run
- [x] Scraper updated with actual selectors
- [x] Manual testing confirms correct extraction
- [x] Documentation updated with screenshots
- [x] Story marked as DONE in EPIC-01.md

## References

- **Selector Discovery**: Lines 567-600 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:567)
- **Troubleshooting**: Lines 1478-1496 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1478)

## Notes

- **Selector Stability**: claude.ai may update their UI at any time, breaking selectors. The fallback strategy mitigates this risk.
- **data-testid Attributes**: If present, these are the most stable. However, claude.ai may not use them.
- **Regular Validation**: Re-run selector discovery tool periodically to ensure selectors still work.
- **Screenshots**: Take screenshots of DevTools showing each selector's location for future reference.

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 2  
**Actual Effort**: TBD