"""Shared datetime extraction component enums.

These enums were previously redefined with identical bodies in every backend's
scalar-datetime expression system (Polars, Narwhals, Ibis — both the Substrait
and Mountainash-extension variants). They are backend-agnostic vocabularies for
``extract`` / ``extract_boolean`` and live here as the single source of truth.
"""
from __future__ import annotations

from enum import Enum


class DatetimeComponent(Enum):
    """Datetime component types for extraction."""

    YEAR = "YEAR"
    ISO_YEAR = "ISO_YEAR"
    US_YEAR = "US_YEAR"
    QUARTER = "QUARTER"
    MONTH = "MONTH"
    DAY = "DAY"
    DAY_OF_YEAR = "DAY_OF_YEAR"
    MONDAY_DAY_OF_WEEK = "MONDAY_DAY_OF_WEEK"
    SUNDAY_DAY_OF_WEEK = "SUNDAY_DAY_OF_WEEK"
    MONDAY_WEEK = "MONDAY_WEEK"
    SUNDAY_WEEK = "SUNDAY_WEEK"
    ISO_WEEK = "ISO_WEEK"
    US_WEEK = "US_WEEK"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    SECOND = "SECOND"
    MILLISECOND = "MILLISECOND"
    MICROSECOND = "MICROSECOND"
    NANOSECOND = "NANOSECOND"
    PICOSECOND = "PICOSECOND"
    SUBSECOND = "SUBSECOND"
    UNIX_TIME = "UNIX_TIME"
    TIMEZONE_OFFSET = "TIMEZONE_OFFSET"


class BooleanComponent(Enum):
    """Boolean component types for extraction."""

    IS_LEAP_YEAR = "IS_LEAP_YEAR"
    IS_DST = "IS_DST"


CALENDAR_COMPONENTS: frozenset[str] = frozenset(
    {
        "QUARTER",
        "MONTH",
        "DAY",
        "DAY_OF_YEAR",
        "MONDAY_DAY_OF_WEEK",
        "SUNDAY_DAY_OF_WEEK",
        "MONDAY_WEEK",
        "SUNDAY_WEEK",
        "ISO_WEEK",
        "US_WEEK",
    }
)


__all__ = ["DatetimeComponent", "BooleanComponent", "CALENDAR_COMPONENTS"]
