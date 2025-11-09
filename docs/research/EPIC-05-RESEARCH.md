# EPIC-05 Research: Historical Data Schema Fix

**Date**: 2025-11-09
**Author**: Orchestrator Mode
**Status**: Completed ✅

## Problem Discovery

During test development for EPIC-01-STOR-03 (JSON Data Schema), a test validation failure was discovered:

```
FAILED tests/test_scraper.py::test_data_structure - AssertionError: Missing required field 'historicalData'
```

## Root Cause Analysis

### 1. Specification Review

From EPIC-01.md (line 106):
> **Reliability Requirements**
> - ✅ Historical data retention (7 days, 2016 data points)

From project structure (EPIC-01.md, line 124):
```
data/
└── usage-data.json
```

The specification clearly requires historical data retention, but the fixture file was created without this field.

### 2. Schema Definition

According to EPIC-01-STOR-03 (JSON Data Schema story), the expected structure should include:

**Top-level fields**:
- `lastUpdated`: ISO 8601 timestamp of last scrape
- `metrics`: Current usage metrics object
- `historicalData`: Array of historical data points

**Historical data point schema** (from EPIC-01-STOR-05):
```json
{
  "timestamp": "ISO 8601 string",
  "fourHourUsed": "number (requests)",
  "weekUsed": "number (requests)",
  "opusWeekUsed": "number (requests)"
}
```

### 3. Current Fixture State

The `data/usage-data.json` file currently contains:
```json
{
  "lastUpdated": "...",
  "metrics": {
    "fourHourCap": {...},
    "weekCap": {...},
    "opusWeekCap": {...}
  }
}
```

**Missing**: `historicalData` field

## Recommended Fix

### Minimal Fix Approach ✅

Add the `historicalData` field to the fixture with an empty array as the initial value:

```json
{
  "lastUpdated": "2025-11-09T00:00:00Z",
  "metrics": {
    "fourHourCap": {...},
    "weekCap": {...},
    "opusWeekCap": {...}
  },
  "historicalData": []
}
```

### Why Empty Array?

1. **Initial State**: On first run, there is no historical data yet
2. **Backward Compatible**: Adding a new field with an empty default doesn't break existing code
3. **Type Safe**: Validates that the field is an array, as expected by projection algorithms
4. **Minimal Change**: Smallest possible fix to unblock tests

### Alternative Approaches Considered

❌ **Option 1**: Add sample historical data
- **Rejected**: Would require maintaining fake data, increases complexity
- **Rejected**: Test should work with real or empty data

❌ **Option 2**: Make field optional
- **Rejected**: Field is required by specification
- **Rejected**: Projection algorithms expect this field to exist

✅ **Option 3**: Add empty array (SELECTED)
- **Advantage**: Minimal, correct, and unblocks development
- **Advantage**: Matches real initial state
- **Advantage**: Type-safe and spec-compliant

## Implementation Plan

### File Changes Required

**File**: `data/usage-data.json`

**Change**:
```diff
{
  "lastUpdated": "2025-11-09T00:00:00Z",
  "metrics": {
    "fourHourCap": {...},
    "weekCap": {...},
    "opusWeekCap": {...}
- }
+ },
+ "historicalData": []
}
```

### Verification Steps

1. Apply the change to `data/usage-data.json`
2. Run failing test: `pytest tests/test_scraper.py::test_data_structure`
3. Verify test passes
4. Run full test suite: `pytest tests/`
5. Verify no regressions

### Regression Prevention

Create a dedicated test `test_historical_data_shape` to validate:
- Field exists
- Field is a list
- Empty list is valid
- Non-empty lists contain valid data point structures

## Impact Assessment

### Risk: LOW ✅

**Why low risk?**
- Single field addition with empty default value
- No changes to existing fields or structure
- Backward compatible (existing code ignores unknown fields)
- Test-driven approach ensures correctness

### Affected Components

1. **Data Schema**: `data/usage-data.json` - Add field
2. **Tests**: `tests/test_scraper.py` - Already expects this field
3. **Projection Algorithms**: Will use this field (EPIC-01-STOR-05)
4. **Scraper**: Will populate this field over time (EPIC-01-STOR-02)

### Not Affected

- Overlay UI (reads from metrics, not historicalData directly)
- File watcher (no schema changes to watch logic)
- Session management (scraper internals unchanged)

## Timeline

- **Research**: 1 hour ✅
- **Implementation**: 30 minutes (EPIC-05-STOR-02)
- **Regression Test**: 1 hour (EPIC-05-STOR-03)

**Total**: 2.5 hours

## References

- [EPIC-01.md](../JIRA/EPIC-01.md) - Main specification
- [EPIC-01-STOR-03.md](../JIRA/EPIC-01-STOR-03.md) - JSON Schema story
- [EPIC-01-STOR-05.md](../JIRA/EPIC-01-STOR-05.md) - Projection algorithms

---

**Status**: Research completed, ready for implementation
**Next Step**: EPIC-05-STOR-02 (Implement data patch)
