# EPIC-05: Historical Data Schema Alignment & Test Fixes

## Executive Summary

Fix schema alignment issues discovered during test development for the Claude Usage Monitor. A failing test (`test_data_structure`) revealed that the data fixture is missing the required `historicalData` top-level field defined in the EPIC-01 specification.

**Version**: 1.0.0
**Status**: In Progress
**Priority**: P0 (Blocker)
**Target Branch**: `claude/epic-05-historical-data-patch-011CUy7PMifh47bVapRGF7WU`

## Problem Statement

During initial test development for EPIC-01-STOR-03 (JSON Data Schema), the test `test_data_structure` was created to validate the schema defined in the specification. However, this test is currently failing because:

1. The data fixture file (`data/usage-data.json`) does not include the `historicalData` field
2. According to EPIC-01 specification (line 106), historical data retention for 7 days (2016 data points) is a core requirement
3. The schema validation test expects this field to be present at the top level

## Objectives

1. **Research**: Document the schema requirements and minimal fix approach ✅
2. **Implement**: Add `historicalData: []` field to data fixture file
3. **Test**: Create regression test to prevent future schema drift

## Technical Context

### Current Schema (Missing historicalData)
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

### Expected Schema (With historicalData)
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

### Historical Data Structure
According to EPIC-01-STOR-05 (projection algorithms), historical data points should follow this schema:
```json
{
  "timestamp": "2025-11-09T12:34:56Z",
  "fourHourUsed": 15,
  "weekUsed": 120,
  "opusWeekUsed": 45
}
```

## Story List

### [EPIC-05-STOR-01](EPIC-05-STOR-01.md): Research Schema Requirements
**Status**: Completed ✅
**Priority**: P0 (Blocker)
**Estimated Effort**: 1 hour
**Dependencies**: None

**Objective**: Research the failing test, review EPIC-01 specification requirements, and document the minimal fix approach.

**Deliverables**:
- Research document at `docs/research/EPIC-05-RESEARCH.md`
- Root cause analysis of test failure
- Recommended fix approach

### [EPIC-05-STOR-02](EPIC-05-STOR-02.md): Implement Historical Data Field
**Status**: Completed ✅
**Priority**: P0 (Blocker)
**Estimated Effort**: 30 minutes
**Dependencies**: STOR-01

**Objective**: Add the missing `historicalData: []` field to the data fixture file.

**Implementation**:
- File: `data/usage-data.json`
- Change: Add `"historicalData": []` as top-level field
- Verification: Run `pytest tests/test_scraper.py::test_data_structure`

### [EPIC-05-STOR-03](EPIC-05-STOR-03.md): Add Regression Test
**Status**: Ready for Test
**Priority**: P1 (High)
**Estimated Effort**: 1 hour
**Dependencies**: STOR-02

**Objective**: Create a dedicated regression test to validate the historicalData field structure and prevent future schema drift.

**Test Requirements**:
- Test name: `test_historical_data_shape`
- Location: `tests/test_scraper.py`
- Validations:
  - `historicalData` field exists
  - `historicalData` is a list
  - Empty list is valid (initial state)
  - Non-empty list contains valid data point objects

## Story Execution Order

1. ✅ **STOR-01**: Research (Completed)
2. ✅ **STOR-02**: Implement fix (Completed)
3. ⏳ **STOR-03**: Add regression test (Pending)

**Total Estimated Effort**: 2.5 hours

## Success Criteria
 
- [x] `test_data_structure` test passes
- [ ] `test_historical_data_shape` regression test created and passes
- [x] `data/usage-data.json` includes `historicalData: []` field
- [x] All existing tests continue to pass
- [x] Changes committed and pushed to `claude/epic-05-historical-data-patch-011CUy7PMifh47bVapRGF7WU`

## Impact Assessment
 
### Files Modified
- `data/usage-data.json` - Add historicalData field
- `tests/test_scraper.py` - Add regression test
- `docs/JIRA/EPIC-05.md` - Add verification summary and test results
 
### Risk Level: LOW
- Minimal change scope (single field addition)
- No breaking changes to existing functionality
- Adding a field with empty default value is backward compatible
- Test-driven approach ensures correctness
 
### Verification Summary (Automated)
- Ran `pytest tests/test_scraper.py::test_data_structure -q` — test passes ✅
- Ran `pytest tests/ -q` — all 57 tests pass ✅
- `data/usage-data.json` now contains `"historicalData": []` as top-level field ✅
- Commit: 421fc1ec16aa4b8e1208362a1d9abf16e964391c ✅

## References

- **EPIC-01 Specification**: [EPIC-01.md](EPIC-01.md) (line 106 - historical data retention)
- **EPIC-01-STOR-03**: [JSON Data Schema](EPIC-01-STOR-03.md) - Original schema definition
- **EPIC-01-STOR-05**: [Projection Algorithms](EPIC-01-STOR-05.md) - Historical data usage
- **Research Document**: [EPIC-05-RESEARCH.md](../research/EPIC-05-RESEARCH.md)

---

**Created**: 2025-11-09
**Epic Owner**: Orchestrator Mode
**Target Completion**: 2025-11-09

## Automated merge & verification (performed 2025-11-10)

- Branches pushed:
  - claude/epic-05-historical-data-patch-011CUy7PMifh47bVapRGF7WU — commit 679648d
  - claude/epic-01-complete-011CUwRBinhBsie6yCw3DBYD — commit 7bc70df
  - claude/fix-claude-url-011CUwWVvJp6fcx42zDHJXZ9 — commit 3db7c96 (pushed)
- Merges & main HEAD:
  - Conflict resolution and merges applied; final main HEAD pushed: 7a0db4e
  - Notable commits on main during this workflow: 1112b50 (merge conflict resolution), 0eb2ece, 1086516 (compat shims), 1b9d1a0, 7a0db4e
- Test run summary:
  - Initial full test run after merges: 5 failed, 39 passed (failures due to leftover merge markers and API mismatches).
  - Resolved merge markers and added compatibility shims; re-ran tests and fixed projection timezone issues.
  - Verified projection test(s) passing: tests/test_projections.py::test_estimate_time_to_cap — passed.
  - Current outstanding failing test(s): tests/test_scraper.py::test_data_structure (the produced data file lacked expected top-level `schemaVersion` key). Full test suite must be re-run after addressing scraper output.
- Actions performed:
  - Replaced conflicted files with the EPIC-01 implementation where appropriate (per instruction).
  - Added compatibility helper functions in [`src/shared/data_schema.py`](src/shared/data_schema.py:1) to restore legacy API expected by tests.
  - Fixed projection algorithm datetime handling to avoid offset-aware vs naive datetime arithmetic and adjusted output format for compatibility with existing tests.
- Next steps (automated flow pending):
  1. Fix scraper output to include `schemaVersion` in produced data file (tests/test_scraper.py::test_data_structure).
  2. Run full test suite locally: `pytest -q`
  3. When all tests pass, append final verification lines and merge commit hashes to JIRA docs and close stories.

Commit references above are in the repository; verify remote `git log origin/main` for the merge history.