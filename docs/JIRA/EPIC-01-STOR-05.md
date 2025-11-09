# EPIC-01-STOR-05: Usage Projection Algorithms

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P1 (High)  
**Estimated Effort**: 6 hours  
**Dependencies**: [STOR-03](EPIC-01-STOR-03.md)  
**Assignee**: TBD

## Objective

Implement usage projection algorithms including Simple Moving Average (SMA), linear regression for trend analysis, and time-to-cap estimation to predict when usage limits will be reached.

## Requirements

### Functional Requirements
1. Calculate Simple Moving Average over configurable window (default 12 points = 1 hour)
2. Perform linear regression on historical data to determine usage rate
3. Estimate time when 100% cap will be reached
4. Project usage percentage at next reset time
5. Calculate confidence level based on historical data quantity
6. Integrate projections into data saving workflow

### Technical Requirements
1. **Algorithms**:
   - Simple Moving Average (SMA)
   - Linear Regression (least squares method)
   - Time-to-cap estimation
2. **Input**: Historical data from JSON schema
3. **Output**: Projection fields in currentState for each cap
4. **Performance**: Calculations complete in <100ms
5. **Accuracy**: Use float precision for all calculations

## Acceptance Criteria

- [x] SMA function calculates average over configurable window
- [x] Linear regression calculates usage rate per hour/day
- [x] Time-to-cap estimation returns ISO timestamp or null
- [x] Projection at reset time calculated correctly
- [x] Confidence level assigned based on data quantity
- [x] All functions have unit tests with 90%+ coverage
- [x] Projections integrate into scraper's save_data function
- [x] Documentation includes algorithm explanations

## Implementation

### File Location

Create [`src/overlay/projection_algorithms.py`](../../src/overlay/projection_algorithms.py)

### Code Implementation

```python
# src/overlay/projection_algorithms.py
"""
Usage Projection Algorithms

Implements SMA, linear regression, and time-to-cap estimation
for predicting Claude usage trends.

Reference: compass_artifact document lines 1042-1194
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple


def calculate_sma(data_points: List[float], window: int = 12) -> float:
    """
    Calculate Simple Moving Average.
    
    Args:
        data_points: List of historical usage percentages
        window: Number of points to average (default 12 = 1 hour at 5-min intervals)
    
    Returns:
        Current average rate
    """
    if len(data_points) < window:
        window = len(data_points)
    
    if window == 0:
        return 0.0
    
    recent = data_points[-window:]
    return sum(recent) / len(recent)


def calculate_trend(historical_data: List[Dict[str, Any]], cap_type: str = 'fourHour') -> float:
    """
    Calculate usage trend using linear regression.
    
    Uses least squares method to find the slope (rate of change).
    
    Args:
        historical_data: List of historical data points
        cap_type: Type of cap ('fourHour', 'oneWeek', 'opusOneWeek')
    
    Returns:
        Rate of change per hour
    """
    if len(historical_data) < 2:
        return 0.0
    
    # Extract data points with indices
    points = [(i, point.get(cap_type, 0)) for i, point in enumerate(historical_data)]
    
    # Calculate linear regression using least squares
    n = len(points)
    sum_x = sum(i for i, _ in points)
    sum_y = sum(y for _, y in points)
    sum_xy = sum(i * y for i, y in points)
    sum_x2 = sum(i * i for i, _ in points)
    
    # Avoid division by zero
    denominator = (n * sum_x2 - sum_x * sum_x)
    if denominator == 0:
        return 0.0
    
    # Slope (rate of change per data point)
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    
    # Convert to rate per hour (5-min intervals = 12 per hour)
    rate_per_hour = slope * 12
    
    return round(rate_per_hour, 2)


def estimate_time_to_cap(
    current_usage: float, 
    rate_per_hour: float, 
    cap_limit: float = 100.0
) -> Optional[str]:
    """
    Estimate when usage will reach cap.
    
    Args:
        current_usage: Current usage percentage
        rate_per_hour: Rate of increase per hour
        cap_limit: Cap limit (default 100%)
    
    Returns:
        ISO timestamp when cap will be reached, or None if won't reach
    """
    if rate_per_hour <= 0:
        return None  # Usage decreasing or stable
    
    remaining = cap_limit - current_usage
    
    if remaining <= 0:
        return None  # Already at or over cap
    
    hours_to_cap = remaining / rate_per_hour
    
    if hours_to_cap < 0:
        return None
    
    time_to_cap = datetime.utcnow() + timedelta(hours=hours_to_cap)
    return time_to_cap.isoformat() + 'Z'


def calculate_projection_at_time(
    current_usage: float,
    rate_per_hour: float,
    target_time: str,
    cap_limit: float = 100.0
) -> float:
    """
    Project usage percentage at a specific future time.
    
    Args:
        current_usage: Current usage percentage
        rate_per_hour: Rate of increase per hour
        target_time: ISO timestamp of target time
        cap_limit: Maximum cap percentage (default 100%)
    
    Returns:
        Projected usage percentage at target time (capped at cap_limit)
    """
    try:
        target_dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
        hours_until_target = (target_dt - datetime.utcnow()).total_seconds() / 3600
        
        if hours_until_target < 0:
            # Target time is in the past
            return current_usage
        
        projected = current_usage + (rate_per_hour * hours_until_target)
        return min(projected, cap_limit)
        
    except (ValueError, AttributeError):
        return current_usage


def determine_confidence(data_point_count: int) -> str:
    """
    Determine confidence level based on historical data quantity.
    
    Args:
        data_point_count: Number of historical data points
    
    Returns:
        Confidence level: 'high', 'medium', or 'low'
    """
    if data_point_count >= 24:  # 2+ hours of data
        return 'high'
    elif data_point_count >= 12:  # 1+ hour of data
        return 'medium'
    else:
        return 'low'


def calculate_projections(data: Dict[str, Any]) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Calculate all projections for current state.
    
    Args:
        data: Complete data structure with historicalData
    
    Returns:
        Dictionary of projections for each cap type, or None if insufficient data
    """
    historical = data.get('historicalData', [])
    
    if len(historical) < 2:
        return None
    
    current_state = data.get('currentState', {})
    if not current_state:
        return None
    
    projections = {}
    
    for cap_type in ['fourHour', 'oneWeek', 'opusOneWeek']:
        cap_data = current_state.get(cap_type, {})
        current = cap_data.get('usagePercent', 0)
        reset_time = cap_data.get('resetTime')
        
        if reset_time is None:
            continue
        
        # Calculate trend
        rate_per_hour = calculate_trend(historical, cap_type)
        
        # Calculate SMA for smoothing
        recent_values = [point.get(cap_type, 0) for point in historical[-12:]]
        sma = calculate_sma(recent_values)
        
        # Estimate time to cap
        time_to_cap = estimate_time_to_cap(current, rate_per_hour)
        
        # Project usage at reset time
        projected_at_reset = calculate_projection_at_time(
            current, 
            rate_per_hour, 
            reset_time
        )
        
        # Determine confidence
        confidence = determine_confidence(len(historical))
        
        # Build projection data
        projections[cap_type] = {
            'averageRatePerHour': rate_per_hour,
            'projectedUsageAtReset': round(projected_at_reset, 1),
            'estimatedTimeToLimit': time_to_cap,
            'confidence': confidence,
            'sma': round(sma, 1)
        }
        
        # Add daily rate for week-based caps
        if 'Week' in cap_type:
            rate_per_day = rate_per_hour * 24
            projections[cap_type]['averageRatePerDay'] = round(rate_per_day, 2)
    
    return projections


def integrate_projections_into_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate projections and integrate them into data structure.
    
    This function should be called by the scraper after updating historical data
    but before writing to file.
    
    Args:
        data: Complete data structure
    
    Returns:
        Data structure with projection fields added to currentState
    """
    projections = calculate_projections(data)
    
    if projections:
        # Update each cap type with projection data
        for cap_type, projection in projections.items():
            if cap_type in data.get('currentState', {}):
                data['currentState'][cap_type].update(projection)
    
    return data
```

## Testing

### Unit Tests

Create [`tests/test_projections.py`](../../tests/test_projections.py):

```python
# tests/test_projections.py
"""Unit tests for projection algorithms."""

import pytest
from datetime import datetime, timedelta
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
```

Run tests:
```powershell
pytest tests/test_projections.py -v --cov=src/overlay/projection_algorithms
```

## Integration with Scraper

Modify [`src/scraper/claude_usage_monitor.py`](../../src/scraper/claude_usage_monitor.py:480) to integrate projections:

```python
from src.overlay.projection_algorithms import integrate_projections_into_data

async def save_data(self, data: Dict[str, Any]) -> None:
    """Save usage data to JSON file atomically with projections."""
    # ... existing code ...
    
    # Add projections before writing
    new_data = integrate_projections_into_data(new_data)
    
    # Write atomically
    with atomic_write(str(self.data_file), overwrite=True) as f:
        json.dump(new_data, f, indent=2)
```

## Dependencies

### Blocked By
- [STOR-03](EPIC-01-STOR-03.md): JSON Data Schema (operates on historicalData)

### Blocks
- [STOR-10](EPIC-01-STOR-10.md): Testing (validates projection accuracy)

## Definition of Done

- [ ] `projection_algorithms.py` created with all functions
- [ ] SMA calculation works correctly
- [ ] Linear regression calculates accurate trends
- [ ] Time-to-cap estimation returns correct timestamps
- [ ] Projection at reset time calculated correctly
- [ ] Confidence levels assigned appropriately
- [ ] All unit tests written and passing (90%+ coverage)
- [ ] Integration with scraper completed
- [ ] Documentation includes algorithm explanations
- [ ] Story marked as DONE in EPIC-01.md

## References

- **SMA Implementation**: Lines 1046-1066 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1046)
- **Linear Regression**: Lines 1068-1098 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1068)
- **Time-to-Cap**: Lines 1100-1128 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1100)
- **Complete Projection Function**: Lines 1130-1194 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1130)

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 3  
**Actual Effort**: TBD