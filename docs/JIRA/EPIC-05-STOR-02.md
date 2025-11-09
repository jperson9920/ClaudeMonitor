# EPIC-05-STOR-02: Implement Historical Data Field

**Status**: Ready for Code
**Priority**: P0 (Blocker)
**Estimated Effort**: 30 minutes
**Dependencies**: EPIC-05-STOR-01 (Completed ✅)

## Objective

Add the missing `historicalData: []` field to the data fixture file to align with EPIC-01 specification and fix the failing `test_data_structure` test.

## Implementation Plan

### File to Modify

**File**: `data/usage-data.json`

### Required Change

Add `"historicalData": []` as a top-level field in the JSON structure.

**Before**:
```json
{
  "lastUpdated": "2025-11-09T00:00:00Z",
  "metrics": {
    "fourHourCap": {...},
    "weekCap": {...},
    "opusWeekCap": {...}
  }
}
```

**After**:
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

1. Represents initial state (no historical data collected yet)
2. Type-safe: validates field is an array
3. Backward compatible: doesn't break existing code
4. Spec-compliant: matches EPIC-01 requirements

## Verification Steps

1. **Create/modify** `data/usage-data.json` with complete fixture structure
2. **Run failing test**:
   ```bash
   pytest tests/test_scraper.py::test_data_structure -v
   ```
3. **Verify**: Test should now pass
4. **Run full suite**:
   ```bash
   pytest tests/ -v
   ```
5. **Verify**: No regressions in other tests

## Acceptance Criteria

- [ ] `data/usage-data.json` file exists with proper structure
- [ ] `historicalData` field added as empty array `[]`
- [ ] File is valid JSON (no syntax errors)
- [ ] `test_data_structure` test passes
- [ ] All existing tests continue to pass
- [ ] Changes committed with descriptive message

## Implementation Details

### Complete Fixture Structure

Create `data/usage-data.json` with this initial structure:

```json
{
  "lastUpdated": "2025-11-09T00:00:00Z",
  "metrics": {
    "fourHourCap": {
      "used": 0,
      "limit": 50,
      "percentage": 0.0
    },
    "weekCap": {
      "used": 0,
      "limit": 1000,
      "percentage": 0.0
    },
    "opusWeekCap": {
      "used": 0,
      "limit": 500,
      "percentage": 0.0
    }
  },
  "historicalData": []
}
```

### Validation

The test `test_data_structure` expects:
- Top-level `lastUpdated` field (ISO 8601 timestamp)
- Top-level `metrics` object
- Top-level `historicalData` array ← **This is the missing field**

## Risk Assessment

**Risk Level**: LOW ✅

- Single field addition
- No breaking changes
- Empty array is safe default
- Test-driven validation

## References

- [EPIC-05 Research Document](../research/EPIC-05-RESEARCH.md)
- [EPIC-01-STOR-03: JSON Data Schema](EPIC-01-STOR-03.md)

---

**Ready for**: Implementation
**Next Story**: EPIC-05-STOR-03 (Add regression test)
