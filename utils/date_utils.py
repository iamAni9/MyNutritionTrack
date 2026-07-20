"""Date and timezone utilities for the nutrition dashboard.

Handles India timezone (Asia/Kolkata) conversions, date formatting,
and date range generation for trend views.
"""

from datetime import datetime, timedelta
from typing import List, Tuple
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
    return get_date_range(end_date, 7)


def get_date_range(end_date: datetime, days: int) -> List[datetime]:
    """Return a list of `days` dates ending on end_date (inclusive), oldest first.

    Args:
        end_date: The last day of the range (inclusive).
        days: Number of days to include.

    Returns:
        List of datetime objects, oldest first.
    """
    dates = []
    for i in range(days - 1, -1, -1):
        dates.append(end_date - timedelta(days=i))
    return dates


def get_month_range(end_date: datetime) -> List[datetime]:
    """Return a list of 30 dates ending on end_date (inclusive), oldest first."""
    return get_date_range(end_date, 30)


def get_quarter_range(end_date: datetime) -> List[datetime]:
    """Return a list of 90 dates ending on end_date (inclusive), oldest first."""
    return get_date_range(end_date, 90)


def format_display_date(dt: datetime) -> str:
    """Return a human-friendly date string, e.g. 'Mon, 04 Jul 2026'."""
    return dt.strftime("%a, %d %b %Y")


def format_short_date(dt: datetime) -> str:
    """Return a compact date string for chart labels, e.g. 'Jul 04'."""
    return dt.strftime("%b %d")


def get_date_bounds(dates: List[datetime]) -> Tuple[datetime, datetime]:
    """Return (min_date, max_date) from a list of dates."""
    if not dates:
        today = get_today_date_india()
        return today, today
    return min(dates), max(dates)