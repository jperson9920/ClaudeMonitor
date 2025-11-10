"""
Claude Usage Monitor - Data Schema

Defines the JSON data structure and validation for usage data storage.

Reference: EPIC-01-STOR-03 (JSON Data Schema)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


# Schema version
SCHEMA_VERSION = "1.0.0"


def validate_cap_structure(cap_data: Dict[str, Any], cap_name: str) -> List[str]:
    """
    Validate a single cap structure.

    Args:
        cap_data: Cap data dictionary
        cap_name: Name of the cap (for error messages)

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    required_fields = ['used', 'limit', 'percentage']
    for field in required_fields:
        if field not in cap_data:
            errors.append(f"{cap_name} missing required field '{field}'")
        elif not isinstance(cap_data[field], (int, float)):
            errors.append(f"{cap_name}.{field} must be a number")

    # Validate percentage is in valid range
    if 'percentage' in cap_data:
        if not 0 <= cap_data['percentage'] <= 100:
            errors.append(f"{cap_name}.percentage must be between 0 and 100")

    return errors


def validate_historical_data_point(point: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single historical data point.

    Args:
        point: Data point dictionary
        index: Index in array (for error messages)

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    required_fields = ['timestamp', 'fourHourUsed', 'weekUsed', 'opusWeekUsed']
    for field in required_fields:
        if field not in point:
            errors.append(f"Historical data point {index} missing '{field}'")

    # Validate timestamp format
    if 'timestamp' in point:
        if not isinstance(point['timestamp'], str):
            errors.append(f"Historical data point {index} timestamp must be string")
        else:
            try:
                datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                errors.append(f"Historical data point {index} has invalid timestamp format")

    # Validate numeric fields
    for field in ['fourHourUsed', 'weekUsed', 'opusWeekUsed']:
        if field in point and not isinstance(point[field], (int, float)):
            errors.append(f"Historical data point {index} {field} must be a number")
        if field in point and point[field] < 0:
            errors.append(f"Historical data point {index} {field} must be non-negative")

    return errors


def validate_usage_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate the complete usage data structure.

    Args:
        data: Complete data dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check top-level structure
    required_top_level = ['lastUpdated', 'metrics', 'historicalData']
    for field in required_top_level:
        if field not in data:
            errors.append(f"Missing required top-level field '{field}'")

    # Validate lastUpdated
    if 'lastUpdated' in data:
        if not isinstance(data['lastUpdated'], str):
            errors.append("lastUpdated must be a string (ISO 8601 format)")
        else:
            try:
                datetime.fromisoformat(data['lastUpdated'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                errors.append("lastUpdated has invalid ISO 8601 format")

    # Validate metrics structure
    if 'metrics' in data:
        metrics = data['metrics']
        if not isinstance(metrics, dict):
            errors.append("metrics must be an object")
        else:
            required_caps = ['fourHourCap', 'weekCap', 'opusWeekCap']
            for cap_name in required_caps:
                if cap_name not in metrics:
                    errors.append(f"metrics missing required cap '{cap_name}'")
                else:
                    errors.extend(validate_cap_structure(metrics[cap_name], cap_name))

    # Validate historicalData
    if 'historicalData' in data:
        if not isinstance(data['historicalData'], list):
            errors.append("historicalData must be an array")
        else:
            for i, point in enumerate(data['historicalData']):
                errors.extend(validate_historical_data_point(point, i))

    return errors


def create_empty_data_structure() -> Dict[str, Any]:
    """
    Create an empty data structure with all required fields.

    Returns:
        Empty but valid data structure
    """
    return {
        "lastUpdated": datetime.utcnow().isoformat() + 'Z',
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


def is_valid_data(data: Dict[str, Any]) -> bool:
    """
    Check if data structure is valid.

    Args:
        data: Data dictionary to validate

    Returns:
        True if valid, False otherwise
    """
    errors = validate_usage_data(data)
    return len(errors) == 0
