"""
Natural language temporal helpers for user-friendly time-based filtering.

Inspired by Linux tools like journalctl --since "3 minutes ago".

MIGRATION NOTE:
    The filter functions (within_last, older_than, etc.) are now available
    as methods on the .dt namespace for a cleaner API:

    # Old style (still works for backwards compatibility):
    >>> within_last(ma.col("timestamp"), "10 minutes")

    # New style (recommended):
    >>> ma.col("timestamp").dt.within_last("10 minutes")
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

# Re-export utilities from canonical location
from ..core.utils.temporal import (
    TIME_UNITS,
    parse_time_expression,
    to_timedelta,
    to_offset_string,
    time_ago,
    since,
)

if TYPE_CHECKING:
    from .expression_builder import BooleanExpressionAPI


# ========================================
# Standalone filter functions (backwards compatibility)
# ========================================
# NOTE: These are now available as methods on the .dt namespace.
# Prefer: col("timestamp").dt.within_last("10 minutes")


def within_last(column: BooleanExpressionAPI, duration: str) -> BooleanExpressionAPI:
    """
    Create expression for "within last X time".

    NOTE: Prefer using the .dt namespace method:
        >>> col("timestamp").dt.within_last("10 minutes")

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


def within_next(column: BooleanExpressionAPI, duration: str) -> BooleanExpressionAPI:
    """
    Create expression for "within next X time".

    NOTE: Prefer using the .dt namespace method:
        >>> col("scheduled_at").dt.within_next("2 hours")

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


def between_last(
    column: BooleanExpressionAPI,
    start_duration: str,
    end_duration: str = None,
) -> BooleanExpressionAPI:
    """
    Create expression for "between X and Y time ago".

    NOTE: Prefer using the .dt namespace method:
        >>> col("timestamp").dt.between_last("2 hours", "1 hour")

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


def older_than(column: BooleanExpressionAPI, duration: str) -> BooleanExpressionAPI:
    """
    Create expression for "older than X time".

    NOTE: Prefer using the .dt namespace method:
        >>> col("created_at").dt.older_than("7 days")

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


def newer_than(column: BooleanExpressionAPI, duration: str) -> BooleanExpressionAPI:
    """
    Alias for within_last() - create expression for "newer than X time ago".

    NOTE: Prefer using the .dt namespace method:
        >>> col("modified_at").dt.newer_than("3 hours")

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


__all__ = [
    # Parsing utilities (canonical location: core.utils.temporal)
    'TIME_UNITS',
    'parse_time_expression',
    'to_timedelta',
    'to_offset_string',

    # Absolute time functions (canonical location: core.utils.temporal)
    'time_ago',
    'since',

    # Filter expressions (backwards compatibility)
    # Prefer: col("timestamp").dt.within_last("10 minutes")
    'within_last',
    'within_next',
    'between_last',
    'older_than',
    'newer_than',
]
