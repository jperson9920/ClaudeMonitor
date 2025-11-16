import re
from typing import Optional
from datetime import datetime
import dateutil.parser

_PERCENT_RE = re.compile(r"(\d{1,3})\s*%")

def parse_percent(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    m = _PERCENT_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None

def parse_datetime(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    try:
        return dateutil.parser.parse(text)
    except Exception:
        return None