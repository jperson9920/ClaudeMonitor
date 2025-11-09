"""
Tests for Claude Usage Monitor projection algorithms.

This module tests the SMA, linear regression, time-to-cap estimation,
and projection calculation functions.
"""

import pytest
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.overlay.projection_algorithms import (
    calculate_sma,
    calculate_trend,
    estimate_time_to_cap,
    calculate_projection_at_time,
    determine_confidence,
    calculate_projections_for_metrics,
    integrate_projections_into_data
)


class TestSMA:
    """Test Simple Moving Average calculations."""

    def test_calculate_sma_full_window(self):
        """Test SMA with exact window size."""
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120]
        result = calculate_sma(data, window=12)
        expected = sum(data) / len(data)
        assert result == expected

    def test_calculate_sma_partial_window(self):
        """Test SMA with smaller dataset than window."""
        data = [10, 20, 30]
        result = calculate_sma(data, window=12)
        assert result == 20.0

    def test_calculate_sma_empty_data(self):
        """Test SMA with empty data."""
        result = calculate_sma([], window=12)
        assert result == 0.0

    def test_calculate_sma_single_point(self):
        """Test SMA with single data point."""
        result = calculate_sma([42], window=12)
        assert result == 42.0


class TestLinearRegression:
    """Test linear regression trend calculations."""

    def test_calculate_trend_increasing(self):
        """Test trend with increasing usage."""
        historical = [
            {'fourHourUsed': 10},
            {'fourHourUsed': 20},
            {'fourHourUsed': 30},
            {'fourHourUsed': 40},
            {'fourHourUsed': 50},
            {'fourHourUsed': 60}
        ]
        rate = calculate_trend(historical, 'fourHourUsed')
        assert rate > 0  # Should be positive trend

    def test_calculate_trend_stable(self):
        """Test trend with stable usage."""
        historical = [
            {'fourHourUsed': 50},
            {'fourHourUsed': 50},
            {'fourHourUsed': 50}
        ]
        rate = calculate_trend(historical, 'fourHourUsed')
        assert rate == 0.0

    def test_calculate_trend_decreasing(self):
        """Test trend with decreasing usage."""
        historical = [
            {'fourHourUsed': 60},
            {'fourHourUsed': 50},
            {'fourHourUsed': 40},
            {'fourHourUsed': 30}
        ]
        rate = calculate_trend(historical, 'fourHourUsed')
        assert rate < 0  # Should be negative trend

    def test_calculate_trend_insufficient_data(self):
        """Test trend with insufficient data."""
        historical = [{'fourHourUsed': 10}]
        rate = calculate_trend(historical, 'fourHourUsed')
        assert rate == 0.0

    def test_calculate_trend_missing_field(self):
        """Test trend with missing field in data."""
        historical = [
            {'otherField': 10},
            {'otherField': 20}
        ]
        rate = calculate_trend(historical, 'fourHourUsed')
        assert rate == 0.0  # All values are 0 (missing field)


class TestTimeToCapEstimation:
    """Test time-to-cap estimation."""

    def test_estimate_time_to_cap_normal(self):
        """Test normal case: 50% usage, 10% per hour rate."""
        current = 50.0
        rate = 10.0
        result = estimate_time_to_cap(current, rate)

        assert result is not None
        result_time = datetime.fromisoformat(result.replace('Z', '+00:00'))
        hours_diff = (result_time - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 4.9 < hours_diff < 5.1  # Should be ~5 hours

    def test_estimate_time_to_cap_negative_rate(self):
        """Test with negative rate (usage decreasing)."""
        result = estimate_time_to_cap(50.0, -10.0)
        assert result is None

    def test_estimate_time_to_cap_zero_rate(self):
        """Test with zero rate (stable usage)."""
        result = estimate_time_to_cap(50.0, 0.0)
        assert result is None

    def test_estimate_time_to_cap_already_at_limit(self):
        """Test when already at cap."""
        result = estimate_time_to_cap(100.0, 10.0)
        assert result is None

    def test_estimate_time_to_cap_over_limit(self):
        """Test when over cap."""
        result = estimate_time_to_cap(105.0, 10.0)
        assert result is None

    def test_estimate_time_to_cap_slow_rate(self):
        """Test with very slow rate."""
        current = 10.0
        rate = 0.1  # Very slow
        result = estimate_time_to_cap(current, rate)

        assert result is not None
        result_time = datetime.fromisoformat(result.replace('Z', '+00:00'))
        hours_diff = (result_time - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 890 < hours_diff < 910  # Should be ~900 hours


class TestProjectionAtTime:
    """Test usage projection at specific time."""

    def test_calculate_projection_normal(self):
        """Test projection 1 hour in future."""
        current = 50.0
        rate = 10.0

        future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
        projected = calculate_projection_at_time(current, rate, future_time)

        assert 59 < projected < 61  # Should be ~60%

    def test_calculate_projection_capped(self):
        """Test projection is capped at 100%."""
        current = 50.0
        rate = 10.0

        future_time = (datetime.utcnow() + timedelta(hours=10)).isoformat() + 'Z'
        projected = calculate_projection_at_time(current, rate, future_time)
        assert projected == 100.0

    def test_calculate_projection_past_time(self):
        """Test projection with time in the past."""
        current = 50.0
        rate = 10.0

        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z'
        projected = calculate_projection_at_time(current, rate, past_time)
        assert projected == current

    def test_calculate_projection_invalid_time(self):
        """Test projection with invalid timestamp."""
        current = 50.0
        rate = 10.0

        projected = calculate_projection_at_time(current, rate, "invalid-timestamp")
        assert projected == current  # Fallback to current


class TestConfidenceDetermination:
    """Test confidence level determination."""

    def test_determine_confidence_high(self):
        """Test high confidence (24+ data points)."""
        assert determine_confidence(30) == 'high'
        assert determine_confidence(24) == 'high'
        assert determine_confidence(100) == 'high'

    def test_determine_confidence_medium(self):
        """Test medium confidence (12-23 data points)."""
        assert determine_confidence(15) == 'medium'
        assert determine_confidence(12) == 'medium'
        assert determine_confidence(23) == 'medium'

    def test_determine_confidence_low(self):
        """Test low confidence (<12 data points)."""
        assert determine_confidence(5) == 'low'
        assert determine_confidence(1) == 'low'
        assert determine_confidence(11) == 'low'

    def test_determine_confidence_edge_cases(self):
        """Test edge cases."""
        assert determine_confidence(0) == 'low'


class TestFullProjections:
    """Test complete projection calculation."""

    def test_calculate_projections_complete(self):
        """Test complete projection calculation with all caps."""
        data = {
            'metrics': {
                'fourHourCap': {
                    'used': 22,
                    'limit': 50,
                    'percentage': 44.0
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
            'historicalData': [
                {'fourHourUsed': 40, 'weekUsed': 28, 'opusWeekUsed': 19},
                {'fourHourUsed': 42, 'weekUsed': 29, 'opusWeekUsed': 19.5},
                {'fourHourUsed': 44, 'weekUsed': 30, 'opusWeekUsed': 20},
            ]
        }

        projections = calculate_projections_for_metrics(data)

        assert projections is not None
        assert 'fourHourCap' in projections
        assert 'weekCap' in projections
        assert 'opusWeekCap' in projections

        # Check required fields
        for cap_type in ['fourHourCap', 'weekCap', 'opusWeekCap']:
            assert 'averageRatePerHour' in projections[cap_type]
            assert 'confidence' in projections[cap_type]
            assert 'sma' in projections[cap_type]

        # Week caps should have daily rate
        assert 'averageRatePerDay' in projections['weekCap']
        assert 'averageRatePerDay' in projections['opusWeekCap']

    def test_calculate_projections_insufficient_data(self):
        """Test projections with insufficient historical data."""
        data = {
            'metrics': {
                'fourHourCap': {'percentage': 50.0}
            },
            'historicalData': [
                {'fourHourUsed': 50}
            ]
        }

        projections = calculate_projections_for_metrics(data)
        assert projections is None

    def test_calculate_projections_no_historical_data(self):
        """Test projections with no historical data."""
        data = {
            'metrics': {
                'fourHourCap': {'percentage': 50.0}
            },
            'historicalData': []
        }

        projections = calculate_projections_for_metrics(data)
        assert projections is None


class TestProjectionIntegration:
    """Test projection integration into data structure."""

    def test_integrate_projections(self):
        """Test projection integration into data structure."""
        data = {
            'metrics': {
                'fourHourCap': {
                    'used': 25,
                    'limit': 50,
                    'percentage': 50.0
                }
            },
            'historicalData': [
                {'fourHourUsed': 48},
                {'fourHourUsed': 49},
                {'fourHourUsed': 50}
            ]
        }

        result = integrate_projections_into_data(data)

        assert 'projections' in result['metrics']['fourHourCap']
        assert 'averageRatePerHour' in result['metrics']['fourHourCap']['projections']
        assert 'confidence' in result['metrics']['fourHourCap']['projections']

    def test_integrate_projections_preserves_data(self):
        """Test that integration preserves existing data."""
        data = {
            'lastUpdated': '2025-11-09T12:00:00Z',
            'metrics': {
                'fourHourCap': {
                    'used': 25,
                    'limit': 50,
                    'percentage': 50.0
                }
            },
            'historicalData': [
                {'fourHourUsed': 48},
                {'fourHourUsed': 49},
                {'fourHourUsed': 50}
            ]
        }

        result = integrate_projections_into_data(data)

        # Original data preserved
        assert result['lastUpdated'] == '2025-11-09T12:00:00Z'
        assert result['metrics']['fourHourCap']['used'] == 25
        assert result['metrics']['fourHourCap']['limit'] == 50
