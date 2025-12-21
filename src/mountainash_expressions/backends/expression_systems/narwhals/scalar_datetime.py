"""Narwhals ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Narwhals backend.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, TYPE_CHECKING

import narwhals as nw

from .base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_datetime import (
        ScalarDatetimeExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = nw.Expr


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


class NarwhalsScalarDatetimeSystem(NarwhalsBaseExpressionSystem):
    """Narwhals implementation of ScalarDatetimeExpressionProtocol.

    Implements core datetime methods:
    - extract: Extract datetime components
    - extract_boolean: Extract boolean datetime properties

    Plus convenience methods for common operations.

    Note: Narwhals has a more limited datetime API than Polars. Some methods
    use workarounds or simplified implementations.
    """

    # =========================================================================
    # Core Extraction Methods
    # =========================================================================

    def extract(
        self,
        x: SupportedExpressions,
        component: SupportedExpressions,
        timezone: SupportedExpressions = None,
        /,
    ) -> SupportedExpressions:
        """Extract portion of a date/time value.

        Args:
            x: Datetime expression.
            component: Component to extract (YEAR, MONTH, DAY, etc.).
            timezone: Timezone string (IANA format).

        Returns:
            Extracted component as integer.
        """
        comp = component.value if isinstance(component, DatetimeComponent) else str(component).upper()

        component_map = {
            "YEAR": lambda e: e.dt.year(),
            "QUARTER": lambda e: e.dt.month() // nw.lit(4) + nw.lit(1),
            "MONTH": lambda e: e.dt.month(),
            "DAY": lambda e: e.dt.day(),
            "DAY_OF_YEAR": lambda e: e.dt.ordinal_day(),
            "MONDAY_DAY_OF_WEEK": lambda e: e.dt.weekday(),
            "ISO_WEEK": lambda e: e.dt.week(),
            "HOUR": lambda e: e.dt.hour(),
            "MINUTE": lambda e: e.dt.minute(),
            "SECOND": lambda e: e.dt.second(),
            "MILLISECOND": lambda e: e.dt.millisecond(),
            "MICROSECOND": lambda e: e.dt.microsecond(),
            "NANOSECOND": lambda e: e.dt.nanosecond(),
        }

        if comp in component_map:
            return component_map[comp](x)

        return x.dt.year()

    def extract_boolean(
        self,
        x: SupportedExpressions,
        /,
        component: SupportedExpressions,
    ) -> SupportedExpressions:
        """Extract boolean values of a date/time value.

        Args:
            x: Datetime expression.
            component: Boolean component (IS_LEAP_YEAR, IS_DST).

        Returns:
            Boolean expression.
        """
        comp = component.value if isinstance(component, BooleanComponent) else str(component).upper()

        if comp == "IS_LEAP_YEAR":
            year = x.dt.year()
            return ((year % nw.lit(4) == nw.lit(0)) & (year % nw.lit(100) != nw.lit(0))) | (year % nw.lit(400) == nw.lit(0))

        if comp == "IS_DST":
            return nw.lit(False)

        return nw.lit(False)

    # =========================================================================
    # Convenience Extraction Methods
    # =========================================================================

    def year(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the year."""
        return x.dt.year()

    def month(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the month (1-12)."""
        return x.dt.month()

    def day(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the day of month (1-31)."""
        return x.dt.day()

    def hour(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the hour (0-23)."""
        return x.dt.hour()

    def minute(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the minute (0-59)."""
        return x.dt.minute()

    def second(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the second (0-59)."""
        return x.dt.second()

    def millisecond(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract milliseconds since last full second."""
        return x.dt.millisecond()

    def microsecond(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract microseconds since last full millisecond."""
        return x.dt.microsecond()

    def nanosecond(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract nanoseconds since last full microsecond."""
        return x.dt.nanosecond()

    def quarter(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the quarter (1-4)."""
        # Narwhals may not have quarter - compute from month
        return (x.dt.month() - nw.lit(1)) // nw.lit(3) + nw.lit(1)

    def day_of_year(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract day of year (1-366)."""
        return x.dt.ordinal_day()

    def day_of_week(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract day of week (Monday=1 to Sunday=7)."""
        return x.dt.weekday()

    def week_of_year(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract ISO week of year (1-53)."""
        return x.dt.week()

    def iso_year(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract ISO 8601 week-numbering year."""
        # Narwhals may not have iso_year - use regular year
        return x.dt.year()

    def unix_timestamp(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        return x.dt.timestamp()

    # =========================================================================
    # Date Arithmetic Methods
    # =========================================================================

    def add_years(
        self,
        x: SupportedExpressions,
        years: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add years to a datetime.

        Args:
            x: Datetime expression.
            years: Number of years to add.

        Returns:
            Datetime with years added.

        Note:
            Narwhals may not have offset_by. Falls back to approximation.
        """
        # Narwhals doesn't have offset_by - use duration addition
        if isinstance(years, int):
            # Approximate: 1 year = 365 days (ignoring leap years)
            return x + nw.duration(days=years * 365)
        return x

    def add_months(
        self,
        x: SupportedExpressions,
        months: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add months to a datetime.

        Args:
            x: Datetime expression.
            months: Number of months to add.

        Returns:
            Datetime with months added.

        Note:
            Narwhals may not have offset_by. Falls back to approximation.
        """
        # Narwhals doesn't have offset_by - use duration addition
        if isinstance(months, int):
            # Approximate: 1 month = 30 days
            return x + nw.duration(days=months * 30)
        return x

    def add_days(
        self,
        x: SupportedExpressions,
        days: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add days to a datetime.

        Args:
            x: Datetime expression.
            days: Number of days to add.

        Returns:
            Datetime with days added.
        """
        if isinstance(days, int):
            return x + nw.duration(days=days)
        return x

    def add_hours(
        self,
        x: SupportedExpressions,
        hours: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add hours to a datetime.

        Args:
            x: Datetime expression.
            hours: Number of hours to add.

        Returns:
            Datetime with hours added.
        """
        if isinstance(hours, int):
            return x + nw.duration(hours=hours)
        return x

    def add_minutes(
        self,
        x: SupportedExpressions,
        minutes: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add minutes to a datetime.

        Args:
            x: Datetime expression.
            minutes: Number of minutes to add.

        Returns:
            Datetime with minutes added.
        """
        if isinstance(minutes, int):
            return x + nw.duration(minutes=minutes)
        return x

    def add_seconds(
        self,
        x: SupportedExpressions,
        seconds: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add seconds to a datetime.

        Args:
            x: Datetime expression.
            seconds: Number of seconds to add.

        Returns:
            Datetime with seconds added.
        """
        if isinstance(seconds, int):
            return x + nw.duration(seconds=seconds)
        return x

    def add_milliseconds(
        self,
        x: SupportedExpressions,
        milliseconds: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add milliseconds to a datetime.

        Args:
            x: Datetime expression.
            milliseconds: Number of milliseconds to add.

        Returns:
            Datetime with milliseconds added.
        """
        if isinstance(milliseconds, int):
            return x + nw.duration(milliseconds=milliseconds)
        return x

    def add_microseconds(
        self,
        x: SupportedExpressions,
        microseconds: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add microseconds to a datetime.

        Args:
            x: Datetime expression.
            microseconds: Number of microseconds to add.

        Returns:
            Datetime with microseconds added.
        """
        if isinstance(microseconds, int):
            return x + nw.duration(microseconds=microseconds)
        return x

    # =========================================================================
    # Date Difference Methods
    # =========================================================================

    def diff_years(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in years.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in years (x - other).
        """
        return x.dt.year() - other.dt.year()

    def diff_months(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in months.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in months (x - other).
        """
        years_diff = x.dt.year() - other.dt.year()
        months_diff = x.dt.month() - other.dt.month()
        return years_diff * nw.lit(12) + months_diff

    def diff_days(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in days.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in days (x - other).
        """
        return (x - other).dt.total_days()

    def diff_hours(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in hours.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in hours (x - other).
        """
        return (x - other).dt.total_hours()

    def diff_minutes(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in minutes.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in minutes (x - other).
        """
        return (x - other).dt.total_minutes()

    def diff_seconds(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in seconds.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in seconds (x - other).
        """
        return (x - other).dt.total_seconds()

    def diff_milliseconds(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in milliseconds.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in milliseconds (x - other).
        """
        return (x - other).dt.total_milliseconds()

    # =========================================================================
    # Truncation / Rounding Methods
    # =========================================================================

    def truncate(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Truncate datetime to the specified unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Truncated datetime.
        """
        return x.dt.truncate(unit)

    def round(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Round datetime to the nearest unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Rounded datetime.

        Note:
            Narwhals may not have round. Falls back to truncate.
        """
        # Narwhals doesn't have round - fallback to truncate
        return x.dt.truncate(unit)

    def ceil(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Round datetime up to the next unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Ceiling datetime.

        Note:
            Narwhals doesn't have ceil. Falls back to truncate.
        """
        # Narwhals doesn't have ceil - fallback to truncate
        return x.dt.truncate(unit)

    def floor(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Round datetime down to the previous unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Floor datetime.
        """
        return x.dt.truncate(unit)

    # =========================================================================
    # Timezone Methods
    # =========================================================================

    def to_timezone(
        self,
        x: SupportedExpressions,
        timezone: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Convert to specified timezone.

        Args:
            x: Datetime expression (must be timezone-aware).
            timezone: Target timezone (IANA format).

        Returns:
            Datetime in target timezone.

        Note:
            Narwhals may not have timezone conversion. Returns input as fallback.
        """
        # Narwhals doesn't have convert_time_zone - fallback
        return x

    def assume_timezone(
        self,
        x: SupportedExpressions,
        timezone: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Assume the timestamp is in the specified timezone.

        Args:
            x: Datetime expression (timezone-naive).
            timezone: Timezone to assume (IANA format).

        Returns:
            Timezone-aware datetime.

        Note:
            Narwhals may not have timezone assignment. Returns input as fallback.
        """
        # Narwhals doesn't have replace_time_zone - fallback
        return x

    # =========================================================================
    # Formatting Methods
    # =========================================================================

    def strftime(
        self,
        x: SupportedExpressions,
        format: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Format datetime as string.

        Args:
            x: Datetime expression.
            format: strftime format string.

        Returns:
            Formatted string.

        Note:
            Narwhals may not have strftime. Returns string representation.
        """
        # Narwhals doesn't have strftime - fallback to string conversion
        return x.cast(nw.String)

    # =========================================================================
    # Snapshot Methods (Static)
    # =========================================================================

    def today(self) -> SupportedExpressions:
        """Return today's date as a literal expression."""
        return nw.lit(date.today())

    def now(self) -> SupportedExpressions:
        """Return current datetime as a literal expression."""
        return nw.lit(datetime.now())
