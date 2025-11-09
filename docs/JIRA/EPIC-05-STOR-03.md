# EPIC-05-STOR-03: Add Regression Test for Historical Data

**Status**: Ready for Test
**Priority**: P1 (High)
**Estimated Effort**: 1 hour
**Dependencies**: EPIC-05-STOR-02 (Implementation)

## Objective

Create a dedicated regression test to validate the `historicalData` field structure and prevent future schema drift.

## Test Requirements

### Test Name
`test_historical_data_shape`

### Location
`tests/test_scraper.py`

### Test Validations

The test should validate:

1. **Field Exists**: `historicalData` is present in the data structure
2. **Correct Type**: `historicalData` is a list (array)
3. **Empty List Valid**: Empty array `[]` is a valid initial state
4. **Data Point Structure**: When non-empty, each item has required fields:
   - `timestamp` (ISO 8601 string)
   - `fourHourUsed` (number)
   - `weekUsed` (number)
   - `opusWeekUsed` (number)

## Implementation Guide

### Test Structure

```python
def test_historical_data_shape():
    """
    Regression test for EPIC-05: Validate historicalData field structure.

    This test ensures that:
    - The historicalData field exists in the data schema
    - The field is a list type
    - Empty list is a valid initial state
    - Non-empty lists contain properly structured data points
    """
    # Load data fixture
    data = load_usage_data()  # Or appropriate helper function

    # 1. Field exists
    assert "historicalData" in data, "Missing required field 'historicalData'"

    # 2. Correct type
    assert isinstance(data["historicalData"], list), \
        "historicalData must be a list"

    # 3. Empty list is valid (initial state)
    # No assertion needed - empty list is acceptable

    # 4. If non-empty, validate structure
    for i, data_point in enumerate(data["historicalData"]):
        assert "timestamp" in data_point, \
            f"Data point {i} missing 'timestamp'"
        assert "fourHourUsed" in data_point, \
            f"Data point {i} missing 'fourHourUsed'"
        assert "weekUsed" in data_point, \
            f"Data point {i} missing 'weekUsed'"
        assert "opusWeekUsed" in data_point, \
            f"Data point {i} missing 'opusWeekUsed'"

        # Validate types
        assert isinstance(data_point["timestamp"], str), \
            f"Data point {i} timestamp must be string"
        assert isinstance(data_point["fourHourUsed"], (int, float)), \
            f"Data point {i} fourHourUsed must be number"
        assert isinstance(data_point["weekUsed"], (int, float)), \
            f"Data point {i} weekUsed must be number"
        assert isinstance(data_point["opusWeekUsed"], (int, float)), \
            f"Data point {i} opusWeekUsed must be number"
```

### Test Scenarios

The test should handle:

1. **Initial State**: Empty `historicalData` array
2. **Populated State**: Array with valid data points
3. **Type Validation**: Ensure fields have correct types
4. **Required Fields**: All mandatory fields present

## Acceptance Criteria

- [ ] Test function `test_historical_data_shape` created in `tests/test_scraper.py`
- [ ] Test validates field existence
- [ ] Test validates field is a list
- [ ] Test accepts empty list as valid
- [ ] Test validates data point structure when non-empty
- [ ] Test includes descriptive docstring
- [ ] Test passes with current fixture
- [ ] Test is included in test suite
- [ ] Test documented in commit message

## Verification Steps

1. **Create test**: Add `test_historical_data_shape` to `tests/test_scraper.py`
2. **Run test**:
   ```bash
   pytest tests/test_scraper.py::test_historical_data_shape -v
   ```
3. **Verify**: Test passes with empty array
4. **Test with sample data**: Temporarily add a data point to verify validation works
5. **Run full suite**:
   ```bash
   pytest tests/ -v
   ```

## Expected Outcome

- Test passes with `historicalData: []` (empty array)
- Test would fail if field is missing
- Test would fail if field is wrong type
- Test would fail if data points have incorrect structure
- Test prevents future schema drift

## Risk Assessment

**Risk Level**: LOW ✅

- Pure test addition, no production code changes
- Validates existing functionality
- Prevents future regressions

## References

- [EPIC-05 Research Document](../research/EPIC-05-RESEARCH.md)
- [EPIC-01-STOR-05: Projection Algorithms](EPIC-01-STOR-05.md) - Historical data usage
- [EPIC-05-STOR-02: Implement Data Patch](EPIC-05-STOR-02.md) - Related implementation

---

**Ready for**: Test Development
**Blocks**: None (nice-to-have quality improvement)
