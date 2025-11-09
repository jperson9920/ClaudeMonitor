# src/scraper/selector_discovery.py
"""
Selector Discovery and Validation Tool

Helps discover and validate selectors for claude.ai/usage page.
Run this script to test selectors against the live page.
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path


async def discover_selectors():
    """Discover and validate selectors on claude.ai/usage."""

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
        print("📄 Navigating to claude.ai/usage...")
        await page.goto('https://claude.ai/usage', wait_until='networkidle')

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

        # Extract all percentage elements
        await extract_all_percentages(page)

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
            print(f"   Error: {type(e).__name__}")


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

    for el in result[:10]:  # Limit to first 10
        print(f"\nTag: {el['tag']}")
        print(f"Class: {el['class']}")
        print(f"ID: {el['id']}")
        print(f"data-testid: {el['testid']}")
        print(f"Text: {el['text']}")


if __name__ == '__main__':
    asyncio.run(discover_selectors())
