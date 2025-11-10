# tests/test_projections.py
"""Unit tests for projection algorithms."""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.overlay.projection_algorithms import (
    calculate_sma,
    calculate_trend,
    estimate_time_to_cap,
    calculate_projection_at_time,
    determine_confidence,
    calculate_projections,
    integrate_projections_into_data
)


def test_calculate_sma():
    """Test Simple Moving Average calculation."""
    # Test with exact window size
    data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
    result = calculate_sma(data, window=12)
    expected = sum(data) / len(data)
    assert result == expected

    # Test with smaller dataset than window
    data = [10, 20, 30]
    result = calculate_sma(data, window=12)
    assert result == 20.0

    # Test with empty data
    result = calculate_sma([], window=12)
    assert result == 0.0


def test_calculate_trend():
    """Test linear regression trend calculation."""
    # Increasing trend
    historical = [
        {'fourHour': 10}, {'fourHour': 20}, {'fourHour': 30},
        {'fourHour': 40}, {'fourHour': 50}, {'fourHour': 60}
    ]
    rate = calculate_trend(historical, 'fourHour')
    assert rate > 0  # Should be positive trend

    # Stable trend
    historical = [
        {'fourHour': 50}, {'fourHour': 50}, {'fourHour': 50}
    ]
    rate = calculate_trend(historical, 'fourHour')
    assert rate == 0.0

    # Insufficient data
    historical = [{'fourHour': 10}]
    rate = calculate_trend(historical, 'fourHour')
    assert rate == 0.0


def test_estimate_time_to_cap():
    """Test time-to-cap estimation."""
    # Normal case: 50% usage, 10% per hour rate -> 5 hours
    current = 50.0
    rate = 10.0
    result = estimate_time_to_cap(current, rate)

    assert result is not None
    result_time = datetime.fromisoformat(result.replace('Z', '+00:00'))
    hours_diff = (result_time - datetime.utcnow()).total_seconds() / 3600
    assert 4.9 < hours_diff < 5.1  # Allow small time delta

    # Negative rate (usage decreasing)
    result = estimate_time_to_cap(50.0, -10.0)
    assert result is None

    # Already at cap
    result = estimate_time_to_cap(100.0, 10.0)
    assert result is None


def test_calculate_projection_at_time():
    """Test usage projection at specific time."""
    current = 50.0
    rate = 10.0

    # 1 hour in future
    future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
    projected = calculate_projection_at_time(current, rate, future_time)

    assert 59 < projected < 61  # Should be ~60% (allow rounding)

    # Cap at 100%
    future_time = (datetime.utcnow() + timedelta(hours=10)).isoformat() + 'Z'
    projected = calculate_projection_at_time(current, rate, future_time)
    assert projected == 100.0


def test_determine_confidence():
    """Test confidence level determination."""
    assert determine_confidence(30) == 'high'
    assert determine_confidence(15) == 'medium'
    assert determine_confidence(5) == 'low'


def test_calculate_projections():
    """Test complete projection calculation."""
    data = {
        'currentState': {
            'fourHour': {
                'usagePercent': 45.0,
                'resetTime': (datetime.utcnow() + timedelta(hours=2)).isoformat() + 'Z'
            },
            'oneWeek': {
                'usagePercent': 60.0,
                'resetTime': (datetime.utcnow() + timedelta(days=3)).isoformat() + 'Z'
            },
            'opusOneWeek': {
                'usagePercent': 20.0,
                'resetTime': (datetime.utcnow() + timedelta(days=3)).isoformat() + 'Z'
            }
        },
        'historicalData': [
            {'fourHour': 40, 'oneWeek': 58, 'opusOneWeek': 19},
            {'fourHour': 42, 'oneWeek': 59, 'opusOneWeek': 19.5},
            {'fourHour': 44, 'oneWeek': 59.5, 'opusOneWeek': 20},
        ]
    }

    projections = calculate_projections(data)

    assert projections is not None
    assert 'fourHour' in projections
    assert 'oneWeek' in projections
    assert 'opusOneWeek' in projections

    # Check required fields
    for cap_type in ['fourHour', 'oneWeek', 'opusOneWeek']:
        assert 'averageRatePerHour' in projections[cap_type]
        assert 'projectedUsageAtReset' in projections[cap_type]
        assert 'confidence' in projections[cap_type]


def test_integrate_projections():
    """Test projection integration into data structure."""
    data = {
        'currentState': {
            'fourHour': {
                'usagePercent': 50.0,
                'resetTime': (datetime.utcnow() + timedelta(hours=2)).isoformat() + 'Z'
            }
        },
        'historicalData': [
            {'fourHour': 48}, {'fourHour': 49}, {'fourHour': 50}
        ]
    }

    result = integrate_projections_into_data(data)

    assert 'averageRatePerHour' in result['currentState']['fourHour']
    assert 'projectedUsageAtReset' in result['currentState']['fourHour']