"""
Tests for Claude Usage Monitor data schema validation.

This module tests the JSON schema validation functions.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.data_schema import (
    validate_cap_structure,
    validate_historical_data_point,
    validate_usage_data,
    create_empty_data_structure,
    is_valid_data
)


class TestCapValidation:
    """Test cap structure validation."""

    def test_valid_cap_structure(self):
        """Test validation with valid cap structure."""
        cap_data = {
            'used': 25,
            'limit': 50,
            'percentage': 50.0
        }
        errors = validate_cap_structure(cap_data, 'testCap')
        assert len(errors) == 0

    def test_cap_missing_field(self):
        """Test validation with missing field."""
        cap_data = {
            'used': 25,
            'limit': 50
            # Missing 'percentage'
        }
        errors = validate_cap_structure(cap_data, 'testCap')
        assert len(errors) > 0
        assert any('percentage' in err for err in errors)

    def test_cap_invalid_type(self):
        """Test validation with invalid field type."""
        cap_data = {
            'used': 'invalid',  # Should be number
            'limit': 50,
            'percentage': 50.0
        }
        errors = validate_cap_structure(cap_data, 'testCap')
        assert len(errors) > 0
        assert any('must be a number' in err for err in errors)

    def test_cap_invalid_percentage_range(self):
        """Test validation with percentage out of range."""
        cap_data = {
            'used': 25,
            'limit': 50,
            'percentage': 150.0  # Over 100%
        }
        errors = validate_cap_structure(cap_data, 'testCap')
        assert len(errors) > 0
        assert any('between 0 and 100' in err for err in errors)


class TestHistoricalDataValidation:
    """Test historical data point validation."""

    def test_valid_historical_point(self):
        """Test validation with valid historical data point."""
        point = {
            'timestamp': '2025-11-09T12:00:00Z',
            'fourHourUsed': 25,
            'weekUsed': 300,
            'opusWeekUsed': 100
        }
        errors = validate_historical_data_point(point, 0)
        assert len(errors) == 0

    def test_historical_point_missing_field(self):
        """Test validation with missing field."""
        point = {
            'timestamp': '2025-11-09T12:00:00Z',
            'fourHourUsed': 25,
            'weekUsed': 300
            # Missing 'opusWeekUsed'
        }
        errors = validate_historical_data_point(point, 0)
        assert len(errors) > 0
        assert any('opusWeekUsed' in err for err in errors)

    def test_historical_point_invalid_timestamp(self):
        """Test validation with invalid timestamp."""
        point = {
            'timestamp': 'not-a-timestamp',
            'fourHourUsed': 25,
            'weekUsed': 300,
            'opusWeekUsed': 100
        }
        errors = validate_historical_data_point(point, 0)
        assert len(errors) > 0
        assert any('timestamp' in err for err in errors)

    def test_historical_point_negative_value(self):
        """Test validation with negative value."""
        point = {
            'timestamp': '2025-11-09T12:00:00Z',
            'fourHourUsed': -10,  # Negative
            'weekUsed': 300,
            'opusWeekUsed': 100
        }
        errors = validate_historical_data_point(point, 0)
        assert len(errors) > 0
        assert any('non-negative' in err for err in errors)


class TestCompleteDataValidation:
    """Test complete data structure validation."""

    def test_valid_complete_data(self):
        """Test validation with valid complete data."""
        data = {
            'lastUpdated': '2025-11-09T12:00:00Z',
            'metrics': {
                'fourHourCap': {
                    'used': 25,
                    'limit': 50,
                    'percentage': 50.0
                },
                'weekCap': {
                    'used': 300,
                    'limit': 1000,
                    'percentage': 30.0
                },
                'opusWeekCap': {
                    'used': 100,
                    'limit': 500,
                    'percentage': 20.0
                }
            },
            'historicalData': []
        }
        errors = validate_usage_data(data)
        assert len(errors) == 0

    def test_data_missing_top_level_field(self):
        """Test validation with missing top-level field."""
        data = {
            'lastUpdated': '2025-11-09T12:00:00Z',
            'metrics': {}
            # Missing 'historicalData'
        }
        errors = validate_usage_data(data)
        assert len(errors) > 0
        assert any('historicalData' in err for err in errors)

    def test_data_invalid_last_updated(self):
        """Test validation with invalid lastUpdated."""
        data = {
            'lastUpdated': 'not-a-timestamp',
            'metrics': {
                'fourHourCap': {'used': 0, 'limit': 50, 'percentage': 0.0},
                'weekCap': {'used': 0, 'limit': 1000, 'percentage': 0.0},
                'opusWeekCap': {'used': 0, 'limit': 500, 'percentage': 0.0}
            },
            'historicalData': []
        }
        errors = validate_usage_data(data)
        assert len(errors) > 0
        assert any('ISO 8601' in err for err in errors)

    def test_data_missing_metric_cap(self):
        """Test validation with missing metric cap."""
        data = {
            'lastUpdated': '2025-11-09T12:00:00Z',
            'metrics': {
                'fourHourCap': {'used': 0, 'limit': 50, 'percentage': 0.0}
                # Missing weekCap and opusWeekCap
            },
            'historicalData': []
        }
        errors = validate_usage_data(data)
        assert len(errors) > 0
        assert any('weekCap' in err for err in errors)
        assert any('opusWeekCap' in err for err in errors)

    def test_data_historical_data_not_list(self):
        """Test validation with historicalData not being a list."""
        data = {
            'lastUpdated': '2025-11-09T12:00:00Z',
            'metrics': {
                'fourHourCap': {'used': 0, 'limit': 50, 'percentage': 0.0},
                'weekCap': {'used': 0, 'limit': 1000, 'percentage': 0.0},
                'opusWeekCap': {'used': 0, 'limit': 500, 'percentage': 0.0}
            },
            'historicalData': {}  # Should be array
        }
        errors = validate_usage_data(data)
        assert len(errors) > 0
        assert any('must be an array' in err for err in errors)


class TestDataStructureCreation:
    """Test empty data structure creation."""

    def test_create_empty_structure(self):
        """Test that created structure is valid."""
        data = create_empty_data_structure()

        # Validate structure
        errors = validate_usage_data(data)
        assert len(errors) == 0

        # Check fields exist
        assert 'lastUpdated' in data
        assert 'metrics' in data
        assert 'historicalData' in data

        # Check metrics
        assert 'fourHourCap' in data['metrics']
        assert 'weekCap' in data['metrics']
        assert 'opusWeekCap' in data['metrics']

        # Check historical data is empty
        assert data['historicalData'] == []

    def test_is_valid_data_function(self):
        """Test is_valid_data helper function."""
        valid_data = create_empty_data_structure()
        assert is_valid_data(valid_data) is True

        invalid_data = {'incomplete': 'data'}
        assert is_valid_data(invalid_data) is False
