"""Date and time utility functions."""

from datetime import datetime, date, timedelta, timezone
from typing import Optional


def now_utc() -> datetime:
    """Get current UTC datetime with timezone info.

    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)


def today_utc() -> date:
    """Get current UTC date.

    Returns:
        Current UTC date
    """
    return now_utc().date()


def days_ago(days: int) -> datetime:
    """Get datetime for N days ago from now (UTC).

    Args:
        days: Number of days in the past

    Returns:
        UTC datetime for N days ago
    """
    return now_utc() - timedelta(days=days)


def days_from_now(days: int) -> datetime:
    """Get datetime for N days from now (UTC).

    Args:
        days: Number of days in the future

    Returns:
        UTC datetime for N days from now
    """
    return now_utc() + timedelta(days=days)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC.

    Args:
        dt: Datetime to convert (if naive, assumed to be UTC)

    Returns:
        UTC datetime with timezone info
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_iso_date(date_str: str) -> Optional[date]:
    """Parse ISO format date string (YYYY-MM-DD).

    Args:
        date_str: Date string in ISO format

    Returns:
        Parsed date or None if invalid
    """
    try:
        return datetime.fromisoformat(date_str).date()
    except (ValueError, AttributeError):
        return None


def format_date(d: date) -> str:
    """Format date as ISO string (YYYY-MM-DD).

    Args:
        d: Date to format

    Returns:
        ISO formatted date string
    """
    return d.isoformat()


def days_between(start: date, end: date) -> int:
    """Calculate number of days between two dates.

    Args:
        start: Start date
        end: End date

    Returns:
        Number of days (positive if end > start)
    """
    return (end - start).days


def is_past(dt: datetime) -> bool:
    """Check if datetime is in the past.

    Args:
        dt: Datetime to check

    Returns:
        True if datetime is in the past
    """
    return to_utc(dt) < now_utc()


def is_future(dt: datetime) -> bool:
    """Check if datetime is in the future.

    Args:
        dt: Datetime to check

    Returns:
        True if datetime is in the future
    """
    return to_utc(dt) > now_utc()
