"""
Natural language temporal helpers for user-friendly time-based filtering.

Inspired by Linux tools like journalctl --since "3 minutes ago".
"""

from __future__ import annotations
import re
from datetime import datetime, timedelta
from typing import Union, Tuple
from .expression_builder import ExpressionBuilder
from ..core.constants import CONST_LOGIC_TYPES


# Time unit mappings for parsing
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
        >>> expr = ma.col("timestamp") > time_ago("5 minutes")
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
        >>> expr = ma.col("timestamp") > since("1 hour")
    """
    if reference is None:
        reference = datetime.now()
    delta = to_timedelta(duration)
    return reference - delta


def within_last(column: ExpressionBuilder, duration: str) -> ExpressionBuilder:
    """
    Create expression for "within last X time".

    Args:
        column: DateTime column expression
        duration: Time expression like "3 minutes", "2 days"

    Returns:
        Boolean expression: column > (now - duration)

    Example:
        >>> # Records from last 10 minutes
        >>> expr = within_last(ma.col("timestamp"), "10 minutes")
        >>> result = df.filter(expr.compile(df))
    """
    threshold = time_ago(duration)
    return column > threshold


def within_next(column: ExpressionBuilder, duration: str) -> ExpressionBuilder:
    """
    Create expression for "within next X time".

    Args:
        column: DateTime column expression
        duration: Time expression like "3 minutes", "2 days"

    Returns:
        Boolean expression: column < (now + duration)

    Example:
        >>> # Records scheduled in next 2 hours
        >>> expr = within_next(ma.col("scheduled_at"), "2 hours")
    """
    delta = to_timedelta(duration)
    threshold = datetime.now() + delta
    return column < threshold


def between_last(column: ExpressionBuilder, start_duration: str, end_duration: str = None) -> ExpressionBuilder:
    """
    Create expression for "between X and Y time ago".

    Args:
        column: DateTime column expression
        start_duration: Start of range (e.g., "2 hours" = 2 hours ago)
        end_duration: End of range (default: "0 seconds" = now)

    Returns:
        Boolean expression: (now - start) <= column <= (now - end)

    Example:
        >>> # Records between 2 hours ago and 1 hour ago
        >>> expr = between_last(ma.col("timestamp"), "2 hours", "1 hour")

        >>> # Records between 1 day ago and now
        >>> expr = between_last(ma.col("timestamp"), "1 day")
    """
    start_time = time_ago(start_duration)

    if end_duration is None:
        end_time = datetime.now()
    else:
        end_time = time_ago(end_duration)

    # Note: start_time is older (smaller) than end_time
    return (column >= start_time) & (column <= end_time)


def older_than(column: ExpressionBuilder, duration: str) -> ExpressionBuilder:
    """
    Create expression for "older than X time".

    Args:
        column: DateTime column expression
        duration: Time expression like "3 minutes", "2 days"

    Returns:
        Boolean expression: column < (now - duration)

    Example:
        >>> # Records older than 7 days
        >>> expr = older_than(ma.col("created_at"), "7 days")
    """
    threshold = time_ago(duration)
    return column < threshold


def newer_than(column: ExpressionBuilder, duration: str) -> ExpressionBuilder:
    """
    Alias for within_last() - create expression for "newer than X time ago".

    Args:
        column: DateTime column expression
        duration: Time expression like "3 minutes", "2 days"

    Returns:
        Boolean expression: column > (now - duration)

    Example:
        >>> # Records newer than 3 hours
        >>> expr = newer_than(ma.col("modified_at"), "3 hours")
    """
    return within_last(column, duration)


# Convenience methods that can be added to ExpressionBuilder
class TemporalFilterMixin:
    """
    Mixin that adds natural language temporal filtering to ExpressionBuilder.

    Usage:
        >>> expr = ma.col("timestamp").within_last("5 minutes")
        >>> expr = ma.col("timestamp").older_than("7 days")
    """

    def within_last(self, duration: str) -> ExpressionBuilder:
        """Filter for timestamps within last X time."""
        return within_last(self, duration)

    def within_next(self, duration: str) -> ExpressionBuilder:
        """Filter for timestamps within next X time."""
        return within_next(self, duration)

    def older_than(self, duration: str) -> ExpressionBuilder:
        """Filter for timestamps older than X time."""
        return older_than(self, duration)

    def newer_than(self, duration: str) -> ExpressionBuilder:
        """Filter for timestamps newer than X time."""
        return newer_than(self, duration)

    def between_last(self, start_duration: str, end_duration: str = None) -> ExpressionBuilder:
        """Filter for timestamps between X and Y time ago."""
        return between_last(self, start_duration, end_duration)


__all__ = [
    # Parsing utilities
    'parse_time_expression',
    'to_timedelta',
    'to_offset_string',

    # Absolute time functions
    'time_ago',
    'since',

    # Filter expressions
    'within_last',
    'within_next',
    'between_last',
    'older_than',
    'newer_than',

    # Mixin for ExpressionBuilder
    'TemporalFilterMixin',
]
