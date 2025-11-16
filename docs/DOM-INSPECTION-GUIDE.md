# DOM Inspection Guide for Claude.ai Usage Selectors

**Story:** EPIC-01-STOR-01  
**Created:** 2025-11-15  
**Status:** Manual inspection required due to Cloudflare protection

## Problem Context

Automated puppeteer access to `https://claude.ai/settings/usage` is blocked by Cloudflare challenge (Ray ID: 99f3b35e1d6a9450). This guide provides step-by-step instructions for **manual DOM inspection** to extract the required CSS selectors.

## Prerequisites

- Chrome or Edge browser (Chromium-based)
- Active Claude.ai Pro subscription with authenticated session
- Basic familiarity with Chrome DevTools

## Inspection Workflow

### Step 1: Open DevTools

1. Open Chrome browser
2. Navigate to: `https://claude.ai/settings/usage`
3. Wait for page to fully load (ensure you're authenticated)
4. Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac) to open DevTools
5. Click the **Elements** tab

### Step 2: Identify Usage Components

You need to locate **3 usage components** on the page:

1. **"Current session"** - Shows current session usage
2. **"Weekly limits — All models"** - Shows weekly usage across all models
3. **"Weekly limits — Opus only"** - Shows weekly Opus-specific usage

### Step 3: Extract Selectors for Each Component

For **each component**, you need to identify:

#### A. Parent Container Selector

1. In DevTools Elements tab, click the **"Select element"** tool (top-left corner icon)
2. Hover over the usage component until the entire card/container is highlighted
3. Click to select it in DevTools
4. Right-click the highlighted element → **Copy** → **Copy selector**
5. Paste into your notes as `css_selector`

**Alternative XPath:**
- Right-click the element → **Copy** → **Copy XPath**
- Paste as `xpath_fallback`

#### B. Percentage Text Selector

1. Within the selected container, find the text showing percentage (e.g., "75% used", "100% used")
2. Click the **"Select element"** tool again
3. Click on the percentage text element
4. Right-click → **Copy** → **Copy selector**
5. Paste as `percentage_selector`

**What to capture:**
- The element containing the **percentage value** (e.g., "75%", "100%")
- Note if it's in a `<span>`, `<div>`, or other tag

#### C. Reset Time Selector

1. Find the text showing reset time (e.g., "Resets in 59 min", "Resets in 3 hours")
2. Click the **"Select element"** tool
3. Click on the reset time text element
4. Right-click → **Copy** → **Copy selector**
5. Paste as `reset_time_selector`

**What to capture:**
- The element containing the **reset time text**
- Note the format (e.g., "Resets in X min/hours")

#### D. Sample HTML

1. In DevTools, right-click the **parent container** element
2. Select **Copy** → **Copy outerHTML**
3. Paste into a text file as `sample_html`
4. **Sanitize sensitive data** (remove any personal identifiers if present)

#### E. Screenshot

1. In DevTools, right-click the **parent container** element
2. Select **Capture node screenshot**
3. Save with filename pattern: `usage-component-{name}.png`
   - `usage-component-current-session.png`
   - `usage-component-weekly-all.png`
   - `usage-component-weekly-opus.png`

### Step 4: Fill Template

Open [`docs/selectors-template.yaml`](./selectors-template.yaml) and fill in the extracted values:

```yaml
selectors:
  last_checked: "2025-11-15T12:00:00Z"  # Update with current timestamp
  inspection_status: "completed"  # Change after filling all values
  cloudflare_bypass: "Manual authentication required"
  
  components:
    - name: "Current session"
      description: "Current session usage component"
      css_selector: "#YOUR_EXTRACTED_CSS_SELECTOR"
      xpath_fallback: "//YOUR_EXTRACTED_XPATH"
      percentage_selector: "#YOUR_PERCENTAGE_SELECTOR"
      reset_time_selector: "#YOUR_RESET_TIME_SELECTOR"
      test_verified: false
      screenshot: "usage-component-current-session.png"
      sample_html: |
        <!-- Paste sanitized HTML here -->
```

## Validation Checklist

Before submitting extracted selectors, verify:

- [ ] All 3 components identified (current session, weekly all, weekly opus)
- [ ] Each component has 4 selectors (parent, percentage, reset time, xpath)
- [ ] Screenshots captured for each component
- [ ] Sample HTML sanitized (no personal data)
- [ ] CSS selectors tested in DevTools Console:
  ```javascript
  document.querySelector('#your-selector-here')  // Should return element
  ```
- [ ] XPath tested in DevTools Console:
  ```javascript
  document.evaluate("//your-xpath-here", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue
  ```

## Testing Selectors in DevTools Console

After extraction, test each selector:

```javascript
// Test CSS selector
const element = document.querySelector('#your-css-selector');
console.log('Element found:', element);
console.log('Text content:', element?.textContent);

// Test XPath
const xpathResult = document.evaluate(
  "//your-xpath-here",
  document,
  null,
  XPathResult.FIRST_ORDERED_NODE_TYPE,
  null
);
console.log('XPath element:', xpathResult.singleNodeValue);

// Test percentage selector
const percentage = document.querySelector('#your-percentage-selector');
console.log('Percentage text:', percentage?.textContent);

// Test reset time selector
const resetTime = document.querySelector('#your-reset-time-selector');
console.log('Reset time text:', resetTime?.textContent);
```

## Common Issues

### Issue 1: Selector Too Specific
**Problem:** Selector includes dynamic IDs (e.g., `#react-12345`)  
**Solution:** Use class-based selectors or data attributes instead

### Issue 2: Multiple Elements Match
**Problem:** `document.querySelectorAll()` returns multiple elements  
**Solution:** Add parent context or use `:nth-child()` to target specific instance

### Issue 3: Element Not Found
**Problem:** Selector returns `null`  
**Solution:** Check for typos, ensure element is in DOM (not lazy-loaded), verify CSS selector syntax

## Output Format

After completing inspection, you should have:

1. **Updated `selectors-template.yaml`** with all values filled
2. **3 screenshots** in `docs/screenshots/` directory
3. **Sample HTML** for each component (sanitized)
4. **Validation tests** confirming selectors work

## Next Steps

1. Complete manual inspection using this guide
2. Fill `docs/selectors-template.yaml` with extracted values
3. Run validation tests in browser console
4. Rename `selectors-template.yaml` → `selectors.yaml`
5. Update [`docs/JIRA/EPIC-01-STOR-01.md`](./JIRA/EPIC-01-STOR-01.md) status to COMPLETED
6. Proceed to EPIC-02-STOR-01 (scraper implementation)

## Reference

- Story: [`docs/JIRA/EPIC-01-STOR-01.md`](./JIRA/EPIC-01-STOR-01.md)
- Research: [`docs/Research.md`](./Research.md) (Section: Cloudflare bypass strategy)
- Template: [`docs/selectors-template.yaml`](./selectors-template.yaml)

---

**Note:** The actual scraper implementation (EPIC-02) will use `undetected-chromedriver` with persistent sessions to bypass Cloudflare automatically. This manual inspection is a one-time setup to obtain initial selectors.