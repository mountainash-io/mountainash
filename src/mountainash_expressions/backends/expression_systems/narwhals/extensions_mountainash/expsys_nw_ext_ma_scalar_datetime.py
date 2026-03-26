"""Narwhals ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Narwhals backend.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarDatetimeExpressionSystemProtocol


if TYPE_CHECKING:
    from mountainash_expressions.types import NarwhalsExpr


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


class MountainAshNarwhalsScalarDatetimeExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarDatetimeExpressionSystemProtocol):
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
        x: NarwhalsExpr,
        component: NarwhalsExpr,
        timezone: NarwhalsExpr = None,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        /,
        component: NarwhalsExpr,
    ) -> NarwhalsExpr:
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

    def year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the year."""
        return x.dt.year()

    def month(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the month (1-12)."""
        return x.dt.month()

    def day(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the day of month (1-31)."""
        return x.dt.day()

    def hour(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the hour (0-23)."""
        return x.dt.hour()

    def minute(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the minute (0-59)."""
        return x.dt.minute()

    def second(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the second (0-59)."""
        return x.dt.second()

    def millisecond(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract milliseconds since last full second."""
        return x.dt.millisecond()

    def microsecond(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract microseconds since last full millisecond."""
        return x.dt.microsecond()

    def nanosecond(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract nanoseconds since last full microsecond."""
        return x.dt.nanosecond()

    def quarter(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the quarter (1-4)."""
        # Narwhals may not have quarter - compute from month
        return (x.dt.month() - nw.lit(1)) // nw.lit(3) + nw.lit(1)

    def day_of_year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract day of year (1-366)."""
        return x.dt.ordinal_day()

    def day_of_week(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract day of week (Monday=1 to Sunday=7)."""
        return x.dt.weekday()

    def week_of_year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract ISO week of year (1-53)."""
        return x.dt.week()

    def iso_year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract ISO 8601 week-numbering year."""
        # Narwhals may not have iso_year - use regular year
        return x.dt.year()

    def unix_timestamp(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        return x.dt.timestamp()

    def timezone_offset(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract timezone offset to UTC in seconds.

        Note: Narwhals doesn't directly expose timezone offset.
        Returns 0 as a placeholder.
        """
        return nw.lit(0)

    def is_leap_year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Check if the year is a leap year."""
        year = x.dt.year()
        return ((year % nw.lit(4) == nw.lit(0)) & (year % nw.lit(100) != nw.lit(0))) | (year % nw.lit(400) == nw.lit(0))

    def is_dst(
        self,
        x: NarwhalsExpr,
        /,
        timezone: str = None,
    ) -> NarwhalsExpr:
        """Check if DST is observed at this time.

        Note: Narwhals doesn't have direct DST detection.
        Returns False as a placeholder.
        """
        return nw.lit(False)

    # =========================================================================
    # Date Arithmetic Methods
    # =========================================================================

    def add_years(
        self,
        x: NarwhalsExpr,
        years: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add years to a datetime.

        Args:
            x: Datetime expression.
            years: Number of years to add.

        Returns:
            Datetime with years added.
        """
        years_val = self._extract_literal_value(years)
        return x.dt.offset_by(f"{int(years_val)}y")

    def add_months(
        self,
        x: NarwhalsExpr,
        months: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add months to a datetime.

        Args:
            x: Datetime expression.
            months: Number of months to add.

        Returns:
            Datetime with months added.
        """
        months_val = self._extract_literal_value(months)
        return x.dt.offset_by(f"{int(months_val)}mo")

    def add_days(
        self,
        x: NarwhalsExpr,
        days: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add days to a datetime.

        Args:
            x: Datetime expression.
            days: Number of days to add.

        Returns:
            Datetime with days added.
        """
        days_val = self._extract_literal_value(days)
        return x.dt.offset_by(f"{int(days_val)}d")

    def add_hours(
        self,
        x: NarwhalsExpr,
        hours: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add hours to a datetime.

        Args:
            x: Datetime expression.
            hours: Number of hours to add.

        Returns:
            Datetime with hours added.
        """
        hours_val = self._extract_literal_value(hours)
        return x.dt.offset_by(f"{int(hours_val)}h")

    def add_minutes(
        self,
        x: NarwhalsExpr,
        minutes: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add minutes to a datetime.

        Args:
            x: Datetime expression.
            minutes: Number of minutes to add.

        Returns:
            Datetime with minutes added.
        """
        minutes_val = self._extract_literal_value(minutes)
        return x.dt.offset_by(f"{int(minutes_val)}m")

    def add_seconds(
        self,
        x: NarwhalsExpr,
        seconds: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add seconds to a datetime.

        Args:
            x: Datetime expression.
            seconds: Number of seconds to add.

        Returns:
            Datetime with seconds added.
        """
        seconds_val = self._extract_literal_value(seconds)
        return x.dt.offset_by(f"{int(seconds_val)}s")

    def add_milliseconds(
        self,
        x: NarwhalsExpr,
        milliseconds: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add milliseconds to a datetime.

        Args:
            x: Datetime expression.
            milliseconds: Number of milliseconds to add.

        Returns:
            Datetime with milliseconds added.

        Note:
            Narwhals offset_by may not support 'ms'. Falls back to microseconds.
        """
        ms_val = self._extract_literal_value(milliseconds)
        # Convert to microseconds: 1ms = 1000us
        return x.dt.offset_by(f"{int(ms_val) * 1000}us")

    def add_microseconds(
        self,
        x: NarwhalsExpr,
        microseconds: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add microseconds to a datetime.

        Args:
            x: Datetime expression.
            microseconds: Number of microseconds to add.

        Returns:
            Datetime with microseconds added.
        """
        us_val = self._extract_literal_value(microseconds)
        return x.dt.offset_by(f"{int(us_val)}us")

    # =========================================================================
    # Date Difference Methods
    # =========================================================================

    def diff_years(
        self,
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Calculate difference in hours.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in hours (x - other).

        Note:
            Narwhals may not have total_hours(). Uses total_seconds() / 3600.
        """
        return ((x - other).dt.total_seconds() / nw.lit(3600)).floor()

    def diff_minutes(
        self,
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Calculate difference in minutes.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in minutes (x - other).

        Note:
            Narwhals may not have total_minutes(). Uses total_seconds() / 60.
        """
        return ((x - other).dt.total_seconds() / nw.lit(60)).floor()

    def diff_seconds(
        self,
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        *,
        unit: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Truncate datetime to the specified unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Truncated datetime.
        """
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    def round(
        self,
        x: NarwhalsExpr,
        *,
        unit: NarwhalsExpr,
    ) -> NarwhalsExpr:
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
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    def ceil(
        self,
        x: NarwhalsExpr,
        *,
        unit: NarwhalsExpr,
    ) -> NarwhalsExpr:
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
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    def floor(
        self,
        x: NarwhalsExpr,
        *,
        unit: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Round datetime down to the previous unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Floor datetime.
        """
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    # =========================================================================
    # Timezone Methods
    # =========================================================================

    def to_timezone(
        self,
        x: NarwhalsExpr,
        timezone: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        timezone: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        format: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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

    def today(self) -> NarwhalsExpr:
        """Return today's date as a literal expression."""
        return nw.lit(date.today())

    def now(self) -> NarwhalsExpr:
        """Return current datetime as a literal expression."""
        return nw.lit(datetime.now())

    # =========================================================================
    # Flexible Duration Offset
    # =========================================================================

    def offset_by(
        self,
        x: NarwhalsExpr,
        *,
        offset: str,
    ) -> NarwhalsExpr:
        """Add/subtract flexible duration from datetime.

        Narwhals offset_by only supports single-unit strings,
        so we use shared temporal helper to parse complex strings
        and apply sequentially.

        Args:
            x: Datetime expression.
            offset: Duration string (e.g., "1d", "2h30m", "-3mo", "1d2h").

        Returns:
            Datetime with offset applied.
        """
        from mountainash_expressions.core.utils.temporal import parse_combined_duration

        offset_val = self._extract_literal_value(offset)
        components = parse_combined_duration(offset_val)

        result = x
        for component in components:
            result = result.dt.offset_by(component)

        return result





    # =========================================================================
    # Snapshot Methods (Static)
    # =========================================================================

    def today(self) -> NarwhalsExpr:
        """Return today's date as a literal expression."""
        return nw.lit(date.today())

    def now(self) -> NarwhalsExpr:
        """Return current datetime as a literal expression."""
        return nw.lit(datetime.now())

    # =========================================================================
    # Flexible Duration Offset
    # =========================================================================

    def offset_by(
        self,
        x: NarwhalsExpr,
        *,
        offset: str,
    ) -> NarwhalsExpr:
        """Add/subtract flexible duration from datetime.

        Narwhals offset_by only supports single-unit strings,
        so we use shared temporal helper to parse complex strings
        and apply sequentially.

        Args:
            x: Datetime expression.
            offset: Duration string (e.g., "1d", "2h30m", "-3mo", "1d2h").

        Returns:
            Datetime with offset applied.
        """
        from mountainash_expressions.core.utils.temporal import parse_combined_duration

        offset_val = self._extract_literal_value(offset)
        components = parse_combined_duration(offset_val)

        result = x
        for component in components:
            result = result.dt.offset_by(component)

        return result



    # =========================================================================
    # Convenience Extraction Methods
    # =========================================================================

    def year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the year."""
        return x.dt.year()

    def month(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the month (1-12)."""
        return x.dt.month()

    def day(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the day of month (1-31)."""
        return x.dt.day()

    def hour(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the hour (0-23)."""
        return x.dt.hour()

    def minute(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the minute (0-59)."""
        return x.dt.minute()

    def second(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the second (0-59)."""
        return x.dt.second()

    def millisecond(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract milliseconds since last full second."""
        return x.dt.millisecond()

    def microsecond(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract microseconds since last full millisecond."""
        return x.dt.microsecond()

    def nanosecond(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract nanoseconds since last full microsecond."""
        return x.dt.nanosecond()

    def quarter(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract the quarter (1-4)."""
        # Narwhals may not have quarter - compute from month
        return (x.dt.month() - nw.lit(1)) // nw.lit(3) + nw.lit(1)

    def day_of_year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract day of year (1-366)."""
        return x.dt.ordinal_day()

    def day_of_week(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract day of week (Monday=1 to Sunday=7)."""
        return x.dt.weekday()

    def week_of_year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract ISO week of year (1-53)."""
        return x.dt.week()

    def iso_year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract ISO 8601 week-numbering year."""
        # Narwhals may not have iso_year - use regular year
        return x.dt.year()

    def unix_timestamp(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        return x.dt.timestamp()

    def timezone_offset(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Extract timezone offset to UTC in seconds.

        Note: Narwhals doesn't directly expose timezone offset.
        Returns 0 as a placeholder.
        """
        return nw.lit(0)

    def is_leap_year(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Check if the year is a leap year."""
        year = x.dt.year()
        return ((year % nw.lit(4) == nw.lit(0)) & (year % nw.lit(100) != nw.lit(0))) | (year % nw.lit(400) == nw.lit(0))

    def is_dst(
        self,
        x: NarwhalsExpr,
        /,
        timezone: str = None,
    ) -> NarwhalsExpr:
        """Check if DST is observed at this time.

        Note: Narwhals doesn't have direct DST detection.
        Returns False as a placeholder.
        """
        return nw.lit(False)

    # =========================================================================
    # Date Arithmetic Methods
    # =========================================================================

    def add_years(
        self,
        x: NarwhalsExpr,
        years: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add years to a datetime.

        Args:
            x: Datetime expression.
            years: Number of years to add.

        Returns:
            Datetime with years added.
        """
        years_val = self._extract_literal_value(years)
        return x.dt.offset_by(f"{int(years_val)}y")

    def add_months(
        self,
        x: NarwhalsExpr,
        months: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add months to a datetime.

        Args:
            x: Datetime expression.
            months: Number of months to add.

        Returns:
            Datetime with months added.
        """
        months_val = self._extract_literal_value(months)
        return x.dt.offset_by(f"{int(months_val)}mo")

    def add_days(
        self,
        x: NarwhalsExpr,
        days: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add days to a datetime.

        Args:
            x: Datetime expression.
            days: Number of days to add.

        Returns:
            Datetime with days added.
        """
        days_val = self._extract_literal_value(days)
        return x.dt.offset_by(f"{int(days_val)}d")

    def add_hours(
        self,
        x: NarwhalsExpr,
        hours: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add hours to a datetime.

        Args:
            x: Datetime expression.
            hours: Number of hours to add.

        Returns:
            Datetime with hours added.
        """
        hours_val = self._extract_literal_value(hours)
        return x.dt.offset_by(f"{int(hours_val)}h")

    def add_minutes(
        self,
        x: NarwhalsExpr,
        minutes: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add minutes to a datetime.

        Args:
            x: Datetime expression.
            minutes: Number of minutes to add.

        Returns:
            Datetime with minutes added.
        """
        minutes_val = self._extract_literal_value(minutes)
        return x.dt.offset_by(f"{int(minutes_val)}m")

    def add_seconds(
        self,
        x: NarwhalsExpr,
        seconds: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add seconds to a datetime.

        Args:
            x: Datetime expression.
            seconds: Number of seconds to add.

        Returns:
            Datetime with seconds added.
        """
        seconds_val = self._extract_literal_value(seconds)
        return x.dt.offset_by(f"{int(seconds_val)}s")

    def add_milliseconds(
        self,
        x: NarwhalsExpr,
        milliseconds: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add milliseconds to a datetime.

        Args:
            x: Datetime expression.
            milliseconds: Number of milliseconds to add.

        Returns:
            Datetime with milliseconds added.

        Note:
            Narwhals offset_by may not support 'ms'. Falls back to microseconds.
        """
        ms_val = self._extract_literal_value(milliseconds)
        # Convert to microseconds: 1ms = 1000us
        return x.dt.offset_by(f"{int(ms_val) * 1000}us")

    def add_microseconds(
        self,
        x: NarwhalsExpr,
        microseconds: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Add microseconds to a datetime.

        Args:
            x: Datetime expression.
            microseconds: Number of microseconds to add.

        Returns:
            Datetime with microseconds added.
        """
        us_val = self._extract_literal_value(microseconds)
        return x.dt.offset_by(f"{int(us_val)}us")

    # =========================================================================
    # Date Difference Methods
    # =========================================================================

    def diff_years(
        self,
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Calculate difference in hours.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in hours (x - other).

        Note:
            Narwhals may not have total_hours(). Uses total_seconds() / 3600.
        """
        return ((x - other).dt.total_seconds() / nw.lit(3600)).floor()

    def diff_minutes(
        self,
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Calculate difference in minutes.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in minutes (x - other).

        Note:
            Narwhals may not have total_minutes(). Uses total_seconds() / 60.
        """
        return ((x - other).dt.total_seconds() / nw.lit(60)).floor()

    def diff_seconds(
        self,
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        other: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        *,
        unit: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Truncate datetime to the specified unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Truncated datetime.
        """
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    def round(
        self,
        x: NarwhalsExpr,
        *,
        unit: NarwhalsExpr,
    ) -> NarwhalsExpr:
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
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    def ceil(
        self,
        x: NarwhalsExpr,
        *,
        unit: NarwhalsExpr,
    ) -> NarwhalsExpr:
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
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    def floor(
        self,
        x: NarwhalsExpr,
        *,
        unit: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Round datetime down to the previous unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Floor datetime.
        """
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    # =========================================================================
    # Timezone Methods
    # =========================================================================

    def to_timezone(
        self,
        x: NarwhalsExpr,
        timezone: str,
        /,
    ) -> NarwhalsExpr:
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

    # =========================================================================
    # Component Extraction
    # =========================================================================

    def date(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        return input.dt.date()

    def time(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        raise NotImplementedError("Narwhals does not support .dt.time()")

    # =========================================================================
    # Calendar Helpers
    # =========================================================================

    def month_start(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        raise NotImplementedError("Narwhals does not support month_start()")

    def month_end(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        raise NotImplementedError("Narwhals does not support month_end()")

    def days_in_month(self, input: NarwhalsExpr, /) -> NarwhalsExpr:
        raise NotImplementedError("Narwhals does not support days_in_month()")
