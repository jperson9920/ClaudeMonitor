"""
Claude Usage Monitor - Usage Projection Algorithms

Implements SMA, linear regression, and time-to-cap estimation
for predicting Claude usage trends.

Reference: EPIC-01-STOR-05 (Usage Projection Algorithms)
"""

from datetime import datetime, timedelta, timezone
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


def calculate_trend(historical_data: List[Dict[str, Any]], cap_type: str = 'fourHourUsed') -> float:
    """
    Calculate usage trend using linear regression.

    Uses least squares method to find the slope (rate of change).

    Args:
        historical_data: List of historical data points
        cap_type: Type of cap field ('fourHourUsed', 'weekUsed', 'opusWeekUsed')

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

    time_to_cap = datetime.now(timezone.utc) + timedelta(hours=hours_to_cap)
    return time_to_cap.isoformat().replace('+00:00', 'Z')


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
        hours_until_target = (target_dt - datetime.now(timezone.utc)).total_seconds() / 3600

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


def calculate_projections_for_metrics(data: Dict[str, Any]) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Calculate all projections for current metrics.

    Args:
        data: Complete data structure with historicalData and metrics

    Returns:
        Dictionary of projections for each cap type, or None if insufficient data
    """
    historical = data.get('historicalData', [])

    if len(historical) < 2:
        return None

    metrics = data.get('metrics', {})
    if not metrics:
        return None

    projections = {}

    # Map cap types to historical data fields
    cap_mappings = {
        'fourHourCap': 'fourHourUsed',
        'weekCap': 'weekUsed',
        'opusWeekCap': 'opusWeekUsed'
    }

    for cap_name, historical_field in cap_mappings.items():
        cap_data = metrics.get(cap_name, {})
        current = cap_data.get('percentage', 0)

        # Calculate trend using historical data
        rate_per_hour = calculate_trend(historical, historical_field)

        # Calculate SMA for smoothing
        recent_values = [point.get(historical_field, 0) for point in historical[-12:]]
        sma = calculate_sma(recent_values)

        # Estimate time to cap
        time_to_cap = estimate_time_to_cap(current, rate_per_hour)

        # Determine confidence
        confidence = determine_confidence(len(historical))

        # Build projection data
        projections[cap_name] = {
            'averageRatePerHour': rate_per_hour,
            'estimatedTimeToLimit': time_to_cap,
            'confidence': confidence,
            'sma': round(sma, 1)
        }

        # Add daily rate for week-based caps
        if 'week' in cap_name.lower():
            rate_per_day = rate_per_hour * 24
            projections[cap_name]['averageRatePerDay'] = round(rate_per_day, 2)

    return projections


def integrate_projections_into_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate projections and integrate them into data structure.

    This function should be called by the scraper after updating historical data
    but before writing to file.

    Args:
        data: Complete data structure

    Returns:
        Data structure with projection fields added to metrics
    """
    projections = calculate_projections_for_metrics(data)

    if projections:
        # Update each cap type with projection data
        for cap_name, projection in projections.items():
            if cap_name in data.get('metrics', {}):
                # Add projection fields to the cap
                data['metrics'][cap_name]['projections'] = projection

    return data
