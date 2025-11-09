"""
Tests for Claude Usage Monitor data scraping and schema validation.

This module tests the data structure and schema compliance for the
usage data fixture used by the scraper component.
"""

import json
import os
from pathlib import Path


def load_usage_data():
    """
    Load the usage data fixture from data/usage-data.json.

    Returns:
        dict: Parsed JSON data structure

    Raises:
        FileNotFoundError: If data file doesn't exist
        json.JSONDecodeError: If data file is invalid JSON
    """
    project_root = Path(__file__).parent.parent
    data_file = project_root / "data" / "usage-data.json"

    if not data_file.exists():
        raise FileNotFoundError(f"Data fixture not found: {data_file}")

    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_data_structure():
    """
    Test that the data fixture contains all required top-level fields.

    This test validates:
    - lastUpdated field exists (ISO 8601 timestamp)
    - metrics object exists with all three cap types
    - historicalData array exists (EPIC-05 fix)

    Related: EPIC-01-STOR-03 (JSON Data Schema)
    Related: EPIC-05-STOR-02 (Historical Data Field)
    """
    data = load_usage_data()

    # Validate top-level structure
    assert "lastUpdated" in data, "Missing required field 'lastUpdated'"
    assert "metrics" in data, "Missing required field 'metrics'"
    assert "historicalData" in data, "Missing required field 'historicalData'"

    # Validate lastUpdated is a string (ISO 8601)
    assert isinstance(data["lastUpdated"], str), \
        "lastUpdated must be a string"

    # Validate metrics structure
    metrics = data["metrics"]
    assert "fourHourCap" in metrics, "Missing metrics.fourHourCap"
    assert "weekCap" in metrics, "Missing metrics.weekCap"
    assert "opusWeekCap" in metrics, "Missing metrics.opusWeekCap"

    # Validate each cap has required fields
    for cap_name in ["fourHourCap", "weekCap", "opusWeekCap"]:
        cap = metrics[cap_name]
        assert "used" in cap, f"{cap_name} missing 'used' field"
        assert "limit" in cap, f"{cap_name} missing 'limit' field"
        assert "percentage" in cap, f"{cap_name} missing 'percentage' field"

        # Validate types
        assert isinstance(cap["used"], (int, float)), \
            f"{cap_name}.used must be a number"
        assert isinstance(cap["limit"], (int, float)), \
            f"{cap_name}.limit must be a number"
        assert isinstance(cap["percentage"], (int, float)), \
            f"{cap_name}.percentage must be a number"

    # Validate historicalData is a list (EPIC-05)
    assert isinstance(data["historicalData"], list), \
        "historicalData must be a list"


def test_historical_data_shape():
    """
    Regression test for EPIC-05: Validate historicalData field structure.

    This test ensures that:
    - The historicalData field exists in the data schema
    - The field is a list type
    - Empty list is a valid initial state
    - Non-empty lists contain properly structured data points

    Each data point should have:
    - timestamp: ISO 8601 string
    - fourHourUsed: number (requests in 4-hour window)
    - weekUsed: number (requests in 1-week window)
    - opusWeekUsed: number (Opus requests in 1-week window)

    Related: EPIC-05-STOR-03 (Regression Test)
    Related: EPIC-01-STOR-05 (Projection Algorithms)
    """
    data = load_usage_data()

    # 1. Field exists
    assert "historicalData" in data, "Missing required field 'historicalData'"

    # 2. Correct type
    assert isinstance(data["historicalData"], list), \
        "historicalData must be a list"

    # 3. Empty list is valid (initial state)
    # No assertion needed - empty list is acceptable

    # 4. If non-empty, validate structure
    for i, data_point in enumerate(data["historicalData"]):
        # Check required fields exist
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
            f"Data point {i} timestamp must be string (ISO 8601)"
        assert isinstance(data_point["fourHourUsed"], (int, float)), \
            f"Data point {i} fourHourUsed must be number"
        assert isinstance(data_point["weekUsed"], (int, float)), \
            f"Data point {i} weekUsed must be number"
        assert isinstance(data_point["opusWeekUsed"], (int, float)), \
            f"Data point {i} opusWeekUsed must be number"

        # Validate timestamp format (basic check for ISO 8601)
        timestamp = data_point["timestamp"]
        assert "T" in timestamp, \
            f"Data point {i} timestamp should be ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)"

        # Validate numeric values are non-negative
        assert data_point["fourHourUsed"] >= 0, \
            f"Data point {i} fourHourUsed must be non-negative"
        assert data_point["weekUsed"] >= 0, \
            f"Data point {i} weekUsed must be non-negative"
        assert data_point["opusWeekUsed"] >= 0, \
            f"Data point {i} opusWeekUsed must be non-negative"
