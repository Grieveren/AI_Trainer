"""Validation utility functions."""

import re
from typing import Optional
from datetime import date


def is_valid_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_password(password: str, min_length: int = 8) -> bool:
    """Validate password meets minimum requirements.

    Args:
        password: Password to validate
        min_length: Minimum password length

    Returns:
        True if password meets requirements
    """
    return len(password) >= min_length


def is_valid_uuid(uuid_str: str) -> bool:
    """Validate UUID format.

    Args:
        uuid_str: UUID string to validate

    Returns:
        True if valid UUID format
    """
    import uuid

    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def is_valid_date_range(start: date, end: date) -> bool:
    """Validate that start date is before or equal to end date.

    Args:
        start: Start date
        end: End date

    Returns:
        True if valid date range
    """
    return start <= end


def is_in_range(value: float, min_val: float, max_val: float) -> bool:
    """Check if value is within range (inclusive).

    Args:
        value: Value to check
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        True if value is in range
    """
    return min_val <= value <= max_val


def normalize_email(email: str) -> str:
    """Normalize email address to lowercase and strip whitespace.

    Args:
        email: Email address

    Returns:
        Normalized email address
    """
    return email.strip().lower()


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize string by stripping whitespace and optionally limiting length.

    Args:
        text: String to sanitize
        max_length: Maximum length (if specified)

    Returns:
        Sanitized string
    """
    sanitized = text.strip()
    if max_length and len(sanitized) > max_length:
        return sanitized[:max_length]
    return sanitized


def is_positive_integer(value: int) -> bool:
    """Check if value is a positive integer.

    Args:
        value: Integer value to check

    Returns:
        True if positive integer
    """
    return isinstance(value, int) and value > 0


def is_non_negative(value: float) -> bool:
    """Check if value is non-negative (>= 0).

    Args:
        value: Value to check

    Returns:
        True if non-negative
    """
    return value >= 0
