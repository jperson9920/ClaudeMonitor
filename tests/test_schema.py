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
