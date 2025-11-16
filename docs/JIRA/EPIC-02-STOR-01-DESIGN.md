# EPIC-02-STOR-01 — Scraper Design

## Summary
This document defines the design for a scraper that extracts usage components from claude.ai settings usage page and produces JSON output suitable for downstream storage and monitoring. It targets three usage components: Current session (3%), Weekly all models (36%), Weekly Opus (19%).

## 1. Architecture Overview

- Target module path: src/scraper/

- Responsibilities:
  - claude_scraper.py: orchestrates fetching and extraction, exposes public API.
  - selectors.py: central place for CSS/XPath selector definitions and prioritized lists.
  - extractors.py: logic to apply selectors, parse percentages, and manage fallbacks.
  - models.py: Pydantic dataclasses (or dataclasses) for output schema and validation.
  - utils.py: helpers (timestamping, text normalization, HTML helpers, logging).

- Core classes:
  - ClaudeScraper: main class with method scrape(html: str) -> List[UsageModel]
  - SelectorSet: structure that holds primary and fallback selectors per component
  - Extractor: stateless functions/methods that take element(s) and return parsed values
  - UsageModel: data model matching JSON schema

- Data flow diagram (linear):
  - [Input HTML] -> [ClaudeScraper.scrape] -> [selectors.lookup] -> [extractors.apply]
  -> [parsing & normalization] -> [models.UsageModel validation] -> [JSON output]

## 2. Selector Strategy

- Goal: robust extraction even when small DOM changes occur. Use prioritized selector lists:
  1. Primary CSS selector
  2. XPath fallback
  3. Text-based search using normalized text fragments
  4. Attribute-based fallback (style width, aria-label, role)

- Primary CSS selectors (inferred from HTML):
  - Container for metrics: `.flex.items-center.gap-3` (contextual container)
  - Label text: `p.text-text-500.whitespace-nowrap.text-sm` (contains "Current session", "All models", "Opus only")
  - Percentage: `span.text-text-300.whitespace-nowrap.w-20.text-right`
  - Progress bar: element with inline `style="width: XX%"` (e.g., `div[style*='width:']`)

- XPath fallback selectors:
  - Label: //p[contains(@class,'text-text-500') and contains(normalize-space(.),'Current session')]
  - Percentage sibling: //p[...]/following-sibling::span[contains(@class,'text-text-300')]
  - Generic percent: //*[matches(text(), '\d+%')]/text()

- Text-based fallback extraction:
  - Search the document for text nodes matching regex `(?i)\b(Current session|All models|Opus only)\b` then look nearby (parent/ancestor) for % text like `\d+%`.

- Selector robustness patterns:
  - Prefer class-based selectors that match multiple classes in order (use contains(@class,'text-text-300') rather than exact match).
  - Use contextual selection: find the label node first, then query the nearest percentage element using relative selectors (CSS sibling, XPath following-sibling, ancestor queries).
  - Normalize whitespace and case when matching text.
  - Limit search scope: when a match is found, restrict subsequent queries to that container to avoid cross-matching other UI elements.
  - Use conservative timeouts for dynamic content when using a live browser (EPIC-02-STOR-02).

## 3. JSON Schema Definition

The output model (one object per usage component):

```json
{
  "component_id": "string",
  "label": "string",
  "percent": "number",
  "raw_text": "string",
  "scraped_at": "ISO 8601 timestamp"
}
```

- component_id: deterministic id (e.g., "current_session", "weekly_all_models", "weekly_opus")
- percent: numeric (0-100) stored as float or int
- raw_text: original matched text fragment for auditing

## 4. Module Structure

```
src/scraper/
├── __init__.py
├── claude_scraper.py       # Main scraper class
├── selectors.py            # Selector definitions
├── extractors.py           # HTML extraction logic
├── models.py               # Data models
└── utils.py                # Utilities

tests/
├── unit/
│   ├── test_extractors.py
│   └── test_selectors.py
└── integration/
    └── test_scraper_e2e.py
```

- Implementation notes:
  - Use lxml or BeautifulSoup + cssselect for parsing. Prefer lxml when XPath is required.
  - models.py should use pydantic.BaseModel for validation (optional dataclasses for simplicity).

## 5. Error Handling Strategy

- Error codes (returned in logs and optionally in output metadata):
  - ERR_NO_LABEL = 1001 (label not found)
  - ERR_NO_PERCENT = 1002 (percent text not found)
  - ERR_PARSE_PERCENT = 1003 (failed to parse numeric percent)
  - ERR_SELECTOR_EXHAUSTED = 1004 (all selectors failed)

- Graceful degradation:
  - If percent cannot be parsed but container found, emit percent = null and include raw_text and error_code.
  - If critical failure (no containers found), return an empty list and log ERR_SELECTOR_EXHAUSTED with context.

- Logging and monitoring:
  - Structured logs (JSON) with fields: timestamp, component_id, selector_used, error_code (nullable), message, sample_html.
  - Emit metrics: extraction_success_rate, selector_failures per component.

## 6. Testing Strategy

- Unit tests:
  - test_selectors.py: verify each selector returns expected element for small HTML fragments (positive and negative cases).
  - test_extractors.py: validate parsing logic for a variety of raw_text inputs (e.g., "3% used", "Used: 36%", "36 %").

- Integration test:
  - test_scraper_e2e.py: load full HTML from docs/manual-inspection-results.md and assert extraction returns three UsageModel objects with expected percents [3,36,19].
  - Output the execution to docs/scraper-output/sample-usage.json (commit artifact).

- Fixtures:
  - Store minimal HTML fragments in tests/fixtures/ for each component.

- Edge cases:
  - Missing percent but progress bar width present -> parse width from style attribute.
  - Percent spelled out ("three percent") -> provide a best-effort parser (optional) or flag parse error.

## 7. CI/CD Requirements

- GitHub Actions workflow (.github/workflows/ci.yml) with steps:
  - Checkout
  - Setup Python 3.10/3.11
  - Install dependencies from requirements.txt or poetry
  - Lint: black --check, flake8
  - Run unit tests: pytest -q
  - Run integration tests (optional on PRs or on main)
  - Coverage reporting: pytest --cov and upload to codecov (or coverage artifact)
  - Fail PRs on lint or test failures

- Branch protection: require passing CI on PR before merge.

## 8. Implementation Tasks (estimates)

- Task 1: Create module structure and base classes — 2h
- Task 2: Implement selector definitions based on HTML analysis — 3h
- Task 3: Build extractor logic with fallbacks — 4h
- Task 4: Add JSON output formatting — 1h
- Task 5: Write unit tests — 3h
- Task 6: Create integration test — 2h
- Task 7: Add CI/CD configuration — 1h
- Task 8: Documentation and error codes — 1h

Total estimate: 17h

## 9. Selector Analysis from HTML

- From docs/manual-inspection-results.md:
  - "Current session" label and "3% used"
  - "All models" label and "36% used"
  - "Opus only" label and "19% used"

- Common DOM patterns:
  - Percentage displayed in <span class="text-text-300 whitespace-nowrap w-20 text-right">3% used</span>
  - Label in <p class="text-text-500 whitespace-nowrap text-sm">Current session</p>
  - Progress represented with inline style width on a progress bar element (e.g., style="width: 36%")

- Recommended primary selector per component example:
  - Current session:
    - CSS: p:contains("Current session") + span.text-text-300
    - XPath: //p[contains(normalize-space(.),"Current session")]/following-sibling::span[contains(@class,"text-text-300")]
  - Weekly all models:
    - CSS: p:contains("All models") ~ span.text-text-300
    - XPath: //p[contains(.,"All models")]/../descendant::span[contains(@class,"text-text-300")]
  - Weekly Opus:
    - CSS: p:contains("Opus only") + span.text-text-300
    - XPath: //p[contains(.,"Opus only")]/following::span[contains(@class,"text-text-300")][1]

## 10. Follow-up Stories

- EPIC-02-STOR-02: Live page validation with undetected-chromedriver (rendered content, auth flow)
- EPIC-02-STOR-03: Scheduler and periodic collection (cron/Windows task)
- EPIC-02-STOR-04: Persistent storage and schema migration (sqlite/postgres + Alembic)
- EPIC-02-STOR-05: Monitoring and alerting (Prometheus/CloudWatch + alert rules)

---
Document saved to docs/JIRA/EPIC-02-STOR-01-DESIGN.md. Reference this file during implementation and include EPIC ID in commits and tests.