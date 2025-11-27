"""
Pure temporal utility functions for parsing and calculating time expressions.

These are Python-only utilities with no AST or expression dependencies.
Inspired by Linux tools like journalctl --since "3 minutes ago".
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Tuple


# Time unit mappings for parsing natural language time expressions
TIME_UNITS = {
    # Seconds
    's': 'seconds',
    'sec': 'seconds',
    'second': 'seconds',
    'seconds': 'seconds',

    # Minutes
    'm': 'minutes',
    'min': 'minutes',
    'minute': 'minutes',
    'minutes': 'minutes',

    # Hours
    'h': 'hours',
    'hr': 'hours',
    'hour': 'hours',
    'hours': 'hours',

    # Days
    'd': 'days',
    'day': 'days',
    'days': 'days',

    # Weeks
    'w': 'weeks',
    'week': 'weeks',
    'weeks': 'weeks',

    # Months (approximate as 30 days)
    'mo': 'months',
    'month': 'months',
    'months': 'months',

    # Years (approximate as 365 days)
    'y': 'years',
    'yr': 'years',
    'year': 'years',
    'years': 'years',
}


def parse_time_expression(expr: str) -> Tuple[int, str]:
    """
    Parse natural language time expression into amount and unit.

    Args:
        expr: Time expression like "3 minutes", "2 days", "1h"

    Returns:
        Tuple of (amount, unit) where unit is standardized

    Examples:
        >>> parse_time_expression("3 minutes")
        (3, 'minutes')
        >>> parse_time_expression("2h")
        (2, 'hours')
        >>> parse_time_expression("1 day")
        (1, 'days')
    """
    expr = expr.strip().lower()

    # Pattern: optional number + optional space + unit
    # Supports: "3 minutes", "3minutes", "3m"
    pattern = r'(\d+)\s*([a-z]+)'
    match = re.match(pattern, expr)

    if not match:
        raise ValueError(f"Cannot parse time expression: '{expr}'. Expected format like '3 minutes' or '2h'")

    amount = int(match.group(1))
    unit_str = match.group(2)

    if unit_str not in TIME_UNITS:
        raise ValueError(f"Unknown time unit: '{unit_str}'. Valid units: {list(set(TIME_UNITS.values()))}")

    unit = TIME_UNITS[unit_str]
    return amount, unit


def to_timedelta(expr: str) -> timedelta:
    """
    Convert time expression to Python timedelta.

    Args:
        expr: Time expression like "3 minutes", "2 days"

    Returns:
        Python timedelta object

    Note:
        Months are approximated as 30 days, years as 365 days.
    """
    amount, unit = parse_time_expression(expr)

    if unit == 'months':
        # Approximate: 1 month = 30 days
        return timedelta(days=amount * 30)
    elif unit == 'years':
        # Approximate: 1 year = 365 days
        return timedelta(days=amount * 365)
    else:
        # Use timedelta directly
        kwargs = {unit: amount}
        return timedelta(**kwargs)


def to_offset_string(expr: str) -> str:
    """
    Convert time expression to Polars/Narwhals offset string format.

    Args:
        expr: Time expression like "3 minutes", "2 days"

    Returns:
        Offset string like "3m", "2d"
    """
    amount, unit = parse_time_expression(expr)

    # Map to Polars duration codes
    unit_codes = {
        'seconds': 's',
        'minutes': 'm',
        'hours': 'h',
        'days': 'd',
        'weeks': 'w',
        'months': 'mo',
        'years': 'y',
    }

    code = unit_codes[unit]
    return f"{amount}{code}"


def time_ago(duration: str) -> datetime:
    """
    Calculate absolute datetime for "X time ago".

    Args:
        duration: Time expression like "3 minutes", "2 days"

    Returns:
        Datetime representing current time minus duration

    Example:
        >>> # Get records from last 5 minutes
        >>> threshold = time_ago("5 minutes")
        >>> expr = ma.col("timestamp").gt(threshold)
    """
    delta = to_timedelta(duration)
    return datetime.now() - delta


def since(duration: str, reference: datetime = None) -> datetime:
    """
    Calculate "since X time ago" from reference point.

    Args:
        duration: Time expression like "3 minutes", "2 days"
        reference: Reference datetime (default: now)

    Returns:
        Reference time minus duration

    Example:
        >>> # Records since 1 hour ago
        >>> threshold = since("1 hour")
        >>> expr = ma.col("timestamp").gt(threshold)
    """
    if reference is None:
        reference = datetime.now()
    delta = to_timedelta(duration)
    return reference - delta


__all__ = [
    "TIME_UNITS",
    "parse_time_expression",
    "to_timedelta",
    "to_offset_string",
    "time_ago",
    "since",
]
