"""
Date utilities for the Week Planner system.
"""

from datetime import datetime, timedelta
from typing import Optional
from datetime import datetime
from dateutil import parser, tz

_BKK = tz.gettz("Asia/Bangkok")
_UTC = tz.gettz("UTC")

def normalize_bkk_day(value: str) -> str:
    """
    Accepts ISO datetime/date (UTC or naive-as-UTC), returns YYYY-MM-DD in Asia/Bangkok.
    """
    if not value:
        return None
    dt = parser.isoparse(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_UTC)
    bkk = dt.astimezone(_BKK)
    return bkk.date().isoformat()
