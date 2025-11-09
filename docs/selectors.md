# Claude.ai Usage Page Selectors

**Last Verified**: 2025-11-09
**Page URL**: https://claude.ai/usage

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
- Run `python src/scraper/selector_discovery.py` to validate selectors

## Validation

To validate selectors:

```powershell
python src/scraper/selector_discovery.py
```

This will test all selectors and report which ones work on the current page.
