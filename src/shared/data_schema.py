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
