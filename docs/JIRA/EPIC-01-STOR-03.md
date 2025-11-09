# EPIC-01-STOR-03: JSON Data Schema and Atomic Writes

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 4 hours  
**Dependencies**: [STOR-01](EPIC-01-STOR-01.md)  
**Assignee**: TBD

## Objective

Define the complete JSON data schema for usage data storage and implement atomic write functionality to prevent data corruption. This schema will be used by both the scraper (write) and overlay UI (read) components.

## Requirements

### Functional Requirements
1. Define comprehensive JSON schema with all required fields
2. Implement atomic write wrapper to prevent partial writes
3. Support historical data storage (7 days retention)
4. Include metadata for versioning and timestamps
5. Handle schema migrations gracefully

### Technical Requirements
1. **Schema Version**: 1.0.0
2. **Data Retention**: 2016 historical points (7 days × 24 hours × 12 intervals)
3. **File Format**: JSON with 2-space indentation
4. **Atomic Writes**: Use `atomicwrites` library
5. **File Permissions**: Restrict to current user only (Windows)

## Acceptance Criteria

- [x] JSON schema fully defined with all fields documented
- [x] Schema includes: metadata, currentState, historicalData, alerts
- [x] Atomic write function prevents data corruption
- [x] Historical data automatically trimmed to 7-day window
- [x] Schema validation function implemented
- [x] Example data file provided for testing
- [x] Documentation includes field descriptions and types

## JSON Schema Definition

### Complete Schema Structure

```json
{
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
      "lastReset": "2025-11-08T14:00:00.000Z",
      "projectedUsageAtReset": 82.3,
      "estimatedTimeToLimit": "2025-11-08T17:15:00.000Z",
      "averageRatePerHour": 18.45
    },
    "oneWeek": {
      "usagePercent": 68.5,
      "remaining": 31.5,
      "resetTime": "2025-11-15T00:00:00.000Z",
      "lastReset": "2025-11-08T00:00:00.000Z",
      "projectedUsageAtReset": 95.2,
      "estimatedTimeToLimit": "2025-11-14T18:00:00.000Z",
      "averageRatePerDay": 9.79
    },
    "opusOneWeek": {
      "usagePercent": 23.1,
      "remaining": 76.9,
      "resetTime": "2025-11-15T00:00:00.000Z",
      "lastReset": "2025-11-08T00:00:00.000Z",
      "projectedUsageAtReset": 45.8,
      "estimatedTimeToLimit": null,
      "averageRatePerDay": 3.30
    },
    "timestamp": "2025-11-08T14:30:00.000Z"
  },
  "historicalData": [
    {
      "timestamp": "2025-11-08T14:00:00.000Z",
      "fourHour": 45.2,
      "oneWeek": 68.5,
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
```

### Field Descriptions

#### Schema Version
- **Type**: String (semantic versioning)
- **Purpose**: Track schema version for migrations
- **Example**: `"1.0.0"`

#### Metadata
- `created` (ISO 8601 timestamp): When data file was first created
- `lastUpdate` (ISO 8601 timestamp): Last write time
- `applicationVersion` (string): Application version that wrote data
- `timezone` (string): Always "UTC" for consistency

#### Current State
Contains latest usage data for all three caps:

**Four Hour Cap**:
- `usagePercent` (float): Current usage percentage (0-100)
- `remaining` (float): Remaining percentage (100 - usagePercent)
- `resetTime` (ISO 8601): When this cap resets
- `lastReset` (ISO 8601): When this cap last reset
- `projectedUsageAtReset` (float): Predicted usage at reset time
- `estimatedTimeToLimit` (ISO 8601 or null): When 100% will be reached
- `averageRatePerHour` (float): Usage increase rate per hour

**One Week Cap**: Same structure as Four Hour, plus:
- `averageRatePerDay` (float): Usage increase rate per day

**Opus One Week Cap**: Same structure as One Week Cap

#### Historical Data
Array of historical data points (max 2016 entries):
- `timestamp` (ISO 8601): When data was collected
- `fourHour` (float): 4-hour cap usage percent at this time
- `oneWeek` (float): 1-week cap usage percent at this time
- `opusOneWeek` (float): Opus 1-week cap usage percent at this time

#### Alerts
- `thresholds`: Warning (75%) and critical (90%) thresholds
- `active`: Array of active alerts (empty in v1.0)

## Implementation

### File Location

Create [`src/shared/data_schema.py`](../../src/shared/data_schema.py)

### Code Implementation

```python
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
```

## Testing

### Test Script

Create [`tests/test_schema.py`](../../tests/test_schema.py):

```python
# tests/test_schema.py
"""Test data schema and atomic write functionality."""

import pytest
from pathlib import Path
import json
from src.shared.data_schema import DataSchema, AtomicWriter


def test_empty_schema_creation():
    """Test creating an empty schema."""
    schema = DataSchema.create_empty_schema()
    
    assert schema["schemaVersion"] == "1.0.0"
    assert "metadata" in schema
    assert "currentState" in schema
    assert "historicalData" in schema
    assert isinstance(schema["historicalData"], list)
    assert len(schema["historicalData"]) == 0


def test_schema_validation():
    """Test schema validation."""
    valid_schema = DataSchema.create_empty_schema()
    assert DataSchema.validate_schema(valid_schema) is True
    
    # Invalid schema (missing required field)
    invalid_schema = {"schemaVersion": "1.0.0"}
    assert DataSchema.validate_schema(invalid_schema) is False


def test_historical_data_trimming():
    """Test that historical data is trimmed correctly."""
    schema = DataSchema.create_empty_schema()
    
    # Add more than max points
    for i in range(3000):
        schema["historicalData"].append({
            "timestamp": f"2025-11-08T{i % 24:02d}:00:00.000Z",
            "fourHour": 50.0,
            "oneWeek": 60.0,
            "opusOneWeek": 20.0
        })
    
    trimmed = DataSchema.trim_historical_data(schema)
    assert len(trimmed["historicalData"]) == DataSchema.MAX_HISTORICAL_POINTS


def test_atomic_write_read(tmp_path):
    """Test atomic write and read operations."""
    test_file = tmp_path / "test-data.json"
    test_data = DataSchema.create_empty_schema()
    
    # Write
    AtomicWriter.write_json(test_file, test_data)
    assert test_file.exists()
    
    # Read
    read_data = AtomicWriter.read_json(test_file)
    assert read_data is not None
    assert read_data["schemaVersion"] == test_data["schemaVersion"]


def test_merge_with_existing(tmp_path):
    """Test merging new data with existing file."""
    test_file = tmp_path / "merge-test.json"
    
    # Create initial data
    initial = DataSchema.create_empty_schema()
    initial["historicalData"].append({
        "timestamp": "2025-11-08T14:00:00.000Z",
        "fourHour": 45.0,
        "oneWeek": 68.0,
        "opusOneWeek": 23.0
    })
    AtomicWriter.write_json(test_file, initial)
    
    # Create new data
    new = DataSchema.create_empty_schema()
    new["currentState"] = {"test": "data"}
    
    # Merge
    merged = AtomicWriter.merge_with_existing(test_file, new, preserve_historical=True)
    
    assert len(merged["historicalData"]) == 1
    assert merged["currentState"] == {"test": "data"}
```

Run tests:
```powershell
pytest tests/test_schema.py -v
```

## Dependencies

### Blocked By
- [STOR-01](EPIC-01-STOR-01.md): Project Setup (needs atomicwrites installed)

### Blocks
- [STOR-02](EPIC-01-STOR-02.md): Web Scraper (uses schema for saving data)
- [STOR-04](EPIC-01-STOR-04.md): PyQt5 Overlay UI (reads data using this schema)
- [STOR-05](EPIC-01-STOR-05.md): Usage Projections (operates on historicalData)

## Definition of Done

- [ ] `data_schema.py` created with complete implementation
- [ ] Schema fully documented with all field descriptions
- [ ] Atomic write functions implemented and tested
- [ ] Schema validation function works correctly
- [ ] Historical data trimming works correctly
- [ ] Example data file generated successfully
- [ ] All pytest tests pass
- [ ] Documentation updated
- [ ] Story marked as DONE in EPIC-01.md

## References

- **Schema Definition**: Lines 924-996 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:924)
- **Atomic Writes**: https://github.com/untitaker/python-atomicwrites

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 2  
**Actual Effort**: TBD