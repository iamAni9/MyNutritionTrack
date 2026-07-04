"""Date and timezone utilities for the nutrition dashboard.

Handles India timezone (Asia/Kolkata) conversions, date formatting,
and date range generation for weekly views.
"""

from datetime import datetime, timedelta
from typing import List
import pytz

INDIA_TZ = pytz.timezone("Asia/Kolkata")


def get_today_india() -> datetime:
    """Return current date/time in Asia/Kolkata timezone."""
    return datetime.now(INDIA_TZ)


def get_today_date_india() -> datetime:
    """Return today's date (midnight) in Asia/Kolkata timezone."""
    now = get_today_india()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def format_date(dt: datetime) -> str:
    """Format a datetime as YYYY-MM-DD string."""
    return dt.strftime("%Y-%m-%d")


def parse_date(date_str: str) -> datetime:
    """Parse a YYYY-MM-DD string into a timezone-aware datetime (Asia/Kolkata)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return INDIA_TZ.localize(dt)


def get_week_range(end_date: datetime) -> List[datetime]:
    """Return a list of 7 dates ending on end_date (inclusive), oldest first."""
    dates = []
    for i in range(6, -1, -1):
        dates.append(end_date - timedelta(days=i))
    return dates


def format_display_date(dt: datetime) -> str:
    """Return a human-friendly date string, e.g. 'Mon, 04 Jul 2026'."""
    return dt.strftime("%a, %d %b %Y")
