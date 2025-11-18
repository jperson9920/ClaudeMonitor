import re
import logging
from typing import Optional
from datetime import datetime
import dateutil.parser

logger = logging.getLogger(__name__)

_PERCENT_RE = re.compile(r"(\d{1,3})\s*%")

def parse_percent(text: Optional[str]) -> Optional[float]:
    """
    Backwards-compatible helper that extracts the first integer percent found in text.
    """
    if not text:
        return None
    m = _PERCENT_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def parse_percentage_safe(value_str: str) -> float:
    """
    Parse percentage from string, clamping to 0-100 range.
    Handles: "50%", "50.0%", "50px" (as pixels, not percent), "calc(...)"
    Returns 0.0 on parse failure.
    """
    try:
        if value_str is None:
            return 0.0
        # Remove whitespace
        value_str = value_str.strip()
        lower = value_str.lower()

        # Handle calc() or other CSS functions (treat as complex before greedy '%' check)
        # Prefer explicit "calc(" detection; also treat any alpha+paren pattern (e.g., "min(50%)")
        if "calc(" in lower or re.search(r"[a-zA-Z_][-a-zA-Z0-9_]*\s*\(", value_str):
            logger.warning("complex_css_value", extra={"value": value_str})
            return 0.0  # Can't reliably parse CSS functions like calc()

        # Handle percentage strings
        if '%' in value_str:
            # Only accept a plain numeric percentage (e.g., "50%", "50.0%")
            # Strip the percent sign and any surrounding text like "used"
            # Extract first numeric-like token
            m = re.search(r"(-?\d+(\.\d+)?)", value_str)
            if not m:
                logger.error("percentage_parse_failed", extra={"value": value_str})
                return 0.0
            try:
                num = float(m.group(1))
            except ValueError as e:
                logger.error("percentage_parse_failed", extra={"value": value_str, "error": str(e)})
                return 0.0
            return max(0.0, min(100.0, num))  # Clamp 0-100

        # Handle pixel values - these should NOT be treated as percentages
        if 'px' in lower:
            logger.warning("pixel_value_in_percentage_context", extra={"value": value_str})
            return 0.0  # Don't interpret pixels as percentages

        # Plain number - clamp it
        m = re.search(r"(-?\d+(\.\d+)?)", value_str)
        if not m:
            logger.error("percentage_parse_failed", extra={"value": value_str})
            return 0.0
        try:
            num = float(m.group(1))
        except ValueError as e:
            logger.error("percentage_parse_failed", extra={"value": value_str, "error": str(e)})
            return 0.0
        return max(0.0, min(100.0, num))

    except (ValueError, AttributeError) as e:
        logger.error("percentage_parse_failed", extra={"value": value_str, "error": str(e)})
        return 0.0


def parse_datetime(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    try:
        return dateutil.parser.parse(text)
    except Exception:
        return None