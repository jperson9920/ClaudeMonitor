# src/shared/data_schema.py
"""
Data Schema Definitions and Atomic Write Utilities

Defines the JSON schema for usage data and provides atomic write functions
to prevent data corruption during concurrent access.

Reference: compass_artifact document lines 924-996
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from atomicwrites import atomic_write


class DataSchema:
    """Manages JSON schema for usage data."""

    SCHEMA_VERSION = "1.0.0"
    MAX_HISTORICAL_POINTS = 2016  # 7 days * 24 hours * 12 (5-min intervals)

    @staticmethod
    def create_empty_schema() -> Dict[str, Any]:
        """
        Create an empty schema structure.

        Returns:
            Empty schema dictionary with all required fields
        """
        return {
            "schemaVersion": DataSchema.SCHEMA_VERSION,
            "metadata": {
                "created": datetime.utcnow().isoformat() + 'Z',
                "lastUpdate": datetime.utcnow().isoformat() + 'Z',
                "applicationVersion": "1.0.0",
                "timezone": "UTC"
            },
            "currentState": None,
            "historicalData": [],
            "alerts": {
                "thresholds": {
                    "warning": 75,
                    "critical": 90
                },
                "active": []
            }
        }

    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> bool:
        """
        Validate that data matches expected schema.

        Args:
            data: Data dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required top-level fields
            required_fields = ["schemaVersion", "metadata", "currentState", "historicalData"]
            if not all(field in data for field in required_fields):
                return False

            # Check metadata fields
            metadata_fields = ["lastUpdate", "applicationVersion"]
            if not all(field in data["metadata"] for field in metadata_fields):
                return False

            # Check historicalData is a list
            if not isinstance(data["historicalData"], list):
                return False

            # Validate historical data points
            for point in data["historicalData"]:
                required_point_fields = ["timestamp", "fourHour", "oneWeek", "opusOneWeek"]
                if not all(field in point for field in required_point_fields):
                    return False

            return True

        except (KeyError, TypeError):
            return False

    @staticmethod
    def trim_historical_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trim historical data to maximum allowed points.

        Args:
            data: Data dictionary with historicalData array

        Returns:
            Data with trimmed historical data
        """
        if len(data.get("historicalData", [])) > DataSchema.MAX_HISTORICAL_POINTS:
            data["historicalData"] = data["historicalData"][-DataSchema.MAX_HISTORICAL_POINTS:]
        return data

    @staticmethod
    def recover_corrupted_json(filepath: Path) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover from corrupted JSON file.

        Strategies:
        1. Check for backup file
        2. Try to parse partial JSON
        3. Return empty schema as last resort

        Args:
            filepath: Path to corrupted JSON file

        Returns:
            Recovered data or empty schema
        """
        backup_file = filepath.with_suffix('.json.bak')

        # Try backup file first
        if backup_file.exists():
            print(f'⚠️  Attempting recovery from backup: {backup_file}')
            try:
                with open(backup_file, 'r') as f:
                    data = json.load(f)
                print('✅ Recovered from backup')
                return data
            except Exception as e:
                print(f'❌ Backup also corrupted: {e}')

        # No backup or backup failed - return empty schema
        print('⚠️  Starting with empty schema')
        return DataSchema.create_empty_schema()


class AtomicWriter:
    """Handles atomic writes to prevent data corruption."""

    @staticmethod
    def write_json(filepath: Path, data: Dict[str, Any], indent: int = 2) -> None:
        """
        Write JSON data atomically to file.

        Uses atomic write to ensure file is never partially written,
        preventing corruption from crashes or concurrent access.

        Args:
            filepath: Path to JSON file
            data: Data dictionary to write
            indent: JSON indentation (default 2 spaces)

        Raises:
            IOError: If write fails
        """
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically
        with atomic_write(str(filepath), overwrite=True) as f:
            json.dump(data, f, indent=indent)

    @staticmethod
    def read_json(filepath: Path) -> Optional[Dict[str, Any]]:
        """
        Read JSON data from file.

        Args:
            filepath: Path to JSON file

        Returns:
            Data dictionary if successful, None if file doesn't exist or is invalid
        """
        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Failed to read JSON from {filepath}: {e}")
            return None

    @staticmethod
    def merge_with_existing(
        filepath: Path,
        new_data: Dict[str, Any],
        preserve_historical: bool = True
    ) -> Dict[str, Any]:
        """
        Merge new data with existing data from file.

        Args:
            filepath: Path to existing JSON file
            new_data: New data to merge
            preserve_historical: Whether to preserve historical data array

        Returns:
            Merged data dictionary
        """
        existing = AtomicWriter.read_json(filepath)

        if existing is None:
            # No existing file, use new data as base
            return new_data

        # Preserve historical data if requested
        if preserve_historical and "historicalData" in existing:
            new_data["historicalData"] = existing.get("historicalData", [])

        # Update metadata
        if "metadata" not in new_data:
            new_data["metadata"] = {}

        new_data["metadata"]["lastUpdate"] = datetime.utcnow().isoformat() + 'Z'

        # Preserve creation timestamp
        if "created" in existing.get("metadata", {}):
            new_data["metadata"]["created"] = existing["metadata"]["created"]

        return new_data


# Example usage functions
# Compatibility helpers (legacy function API) required by tests
from typing import Union

def _is_number(value: object) -> bool:
    return isinstance(value, (int, float))

def validate_cap_structure(cap_data: Dict[str, Any], cap_name: str) -> List[str]:
    """
    Backwards-compatible validator for a single cap structure.
    Returns a list of human-readable error messages (empty if valid).
    """
    errors: List[str] = []

    if not isinstance(cap_data, dict):
        errors.append(f"{cap_name}: cap data must be an object")
        return errors

    # used
    if 'used' not in cap_data:
        errors.append(f"{cap_name}: missing 'used'")
    else:
        if not _is_number(cap_data['used']):
            errors.append(f"{cap_name}: 'used' must be a number")

    # limit
    if 'limit' not in cap_data:
        errors.append(f"{cap_name}: missing 'limit'")
    else:
        if not _is_number(cap_data['limit']):
            errors.append(f"{cap_name}: 'limit' must be a number")

    # percentage
    if 'percentage' not in cap_data:
        errors.append(f"{cap_name}: missing 'percentage'")
    else:
        pct = cap_data['percentage']
        if not _is_number(pct):
            errors.append(f"{cap_name}: percentage must be a number")
        else:
            if not (0 <= float(pct) <= 100):
                errors.append(f"{cap_name}: percentage must be between 0 and 100")

    return errors


def validate_historical_data_point(point: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single historical data point. Returns list of errors.
    """
    errors: List[str] = []

    required_fields = ['timestamp', 'fourHourUsed', 'weekUsed', 'opusWeekUsed']
    for field in required_fields:
        if field not in point:
            errors.append(f"point[{index}]: missing '{field}'")

    # Validate timestamp format (ISO 8601)
    ts = point.get('timestamp')
    if ts is not None:
        try:
            datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
        except Exception:
            errors.append(f"point[{index}]: timestamp is not valid ISO 8601")

    # Numeric and non-negative checks
    for numeric_field in ['fourHourUsed', 'weekUsed', 'opusWeekUsed']:
        val = point.get(numeric_field)
        if val is None:
            continue
        if not _is_number(val):
            errors.append(f"point[{index}]: {numeric_field} must be a number")
        else:
            if float(val) < 0:
                errors.append(f"point[{index}]: {numeric_field} must be non-negative")

    return errors


def validate_usage_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate the complete usage data structure. Returns list of errors.
    """
    errors: List[str] = []

    if not isinstance(data, dict):
        errors.append("data must be an object")
        return errors

    # lastUpdated
    last_updated = data.get('lastUpdated')
    if last_updated is None:
        errors.append("missing 'lastUpdated'")
    else:
        try:
            datetime.fromisoformat(str(last_updated).replace('Z', '+00:00'))
        except Exception:
            errors.append("lastUpdated must be ISO 8601")

    # metrics
    metrics = data.get('metrics')
    if not isinstance(metrics, dict):
        errors.append("missing 'metrics' or metrics must be an object")
    else:
        for cap_key in ['fourHourCap', 'weekCap', 'opusWeekCap']:
            if cap_key not in metrics:
                errors.append(f"{cap_key} missing in metrics")
            else:
                errors.extend(validate_cap_structure(metrics.get(cap_key, {}), cap_key))

    # historicalData
    hist = data.get('historicalData')
    if hist is None:
        errors.append("missing 'historicalData'")
    elif not isinstance(hist, list):
        errors.append("historicalData must be an array")
    else:
        for idx, point in enumerate(hist):
            if isinstance(point, dict):
                errors.extend(validate_historical_data_point(point, idx))
            else:
                errors.append(f"historicalData[{idx}] must be an object")

    return errors


def create_empty_data_structure() -> Dict[str, Any]:
    """
    Create an empty data structure compatible with legacy tests.
    """
    return {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'metrics': {
            'fourHourCap': {'used': 0, 'limit': 0, 'percentage': 0.0},
            'weekCap': {'used': 0, 'limit': 0, 'percentage': 0.0},
            'opusWeekCap': {'used': 0, 'limit': 0, 'percentage': 0.0}
        },
        'historicalData': []
    }


def is_valid_data(data: Dict[str, Any]) -> bool:
    """
    Convenience helper returning True if validate_usage_data returns no errors.
    """
    return len(validate_usage_data(data)) == 0

def create_example_data_file(filepath: Path) -> None:
    """Create an example data file for testing."""
    example_data = {
        "schemaVersion": "1.0.0",
        "metadata": {
            "created": "2025-11-08T00:00:00.000Z",
            "lastUpdate": "2025-11-08T14:30:00.000Z",
            "applicationVersion": "1.0.0",
            "timezone": "UTC"
        },
        "currentState": {
            "fourHour": {
                "usagePercent": 45.2,
                "remaining": 54.8,
                "resetTime": "2025-11-08T18:00:00.000Z",
                "lastReset": "2025-11-08T14:00:00.000Z"
            },
            "oneWeek": {
                "usagePercent": 68.5,
                "remaining": 31.5,
                "resetTime": "2025-11-15T00:00:00.000Z",
                "lastReset": "2025-11-08T00:00:00.000Z"
            },
            "opusOneWeek": {
                "usagePercent": 23.1,
                "remaining": 76.9,
                "resetTime": "2025-11-15T00:00:00.000Z",
                "lastReset": "2025-11-08T00:00:00.000Z"
            },
            "timestamp": "2025-11-08T14:30:00.000Z"
        },
        "historicalData": [
            {
                "timestamp": "2025-11-08T14:00:00.000Z",
                "fourHour": 45.2,
                "oneWeek": 68.5,
                "opusOneWeek": 23.1
            },
            {
                "timestamp": "2025-11-08T14:05:00.000Z",
                "fourHour": 45.5,
                "oneWeek": 68.6,
                "opusOneWeek": 23.1
            }
        ],
        "alerts": {
            "thresholds": {
                "warning": 75,
                "critical": 90
            },
            "active": []
        }
    }

    AtomicWriter.write_json(filepath, example_data)
    print(f"✅ Example data file created: {filepath}")

if __name__ == "__main__":
    # Create example data file for testing
    example_file = Path("data/usage-data-example.json")
    create_example_data_file(example_file)

    # Test validation
    data = AtomicWriter.read_json(example_file)
    if data and DataSchema.validate_schema(data):
        print("✅ Schema validation passed")
    else:
        print("❌ Schema validation failed")