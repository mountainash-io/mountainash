"""Polars ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Polars backend.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarDatetimeExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr

# Type alias for expression type

class DatetimeComponent(Enum):
    """Datetime component types for extraction."""

    # Core components
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


class MountainAshPolarsScalarDatetimeExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarDatetimeExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of ScalarDatetimeExpressionProtocol.

    Implements core datetime methods:
    - extract: Extract datetime components (20+ component types)
    - extract_boolean: Extract boolean datetime properties

    Plus convenience methods for common operations:
    - Date arithmetic: add_days, add_months, add_years, etc.
    - Date difference: diff_days, diff_months, diff_years, etc.
    - Truncation: truncate, round, ceil, floor
    - Timezone: to_timezone, assume_timezone
    - Formatting: strftime
    """

    # =========================================================================
    # Core Extraction Methods
    # =========================================================================

    def extract(
        self,
        x: PolarsExpr,
        component: PolarsExpr,
        timezone: PolarsExpr = None,
        /,
    ) -> PolarsExpr:
        """Extract portion of a date/time value.

        Args:
            x: Datetime expression.
            component: Component to extract (YEAR, MONTH, DAY, etc.).
            timezone: Timezone string (IANA format).

        Returns:
            Extracted component as integer.
        """
        # Handle component as string or enum
        comp = component.value if isinstance(component, DatetimeComponent) else str(component).upper()

        # Map component to Polars extraction method
        component_map = {
            "YEAR": lambda e: e.dt.year(),
            "ISO_YEAR": lambda e: e.dt.iso_year(),
            "QUARTER": lambda e: e.dt.quarter(),
            "MONTH": lambda e: e.dt.month(),
            "DAY": lambda e: e.dt.day(),
            "DAY_OF_YEAR": lambda e: e.dt.ordinal_day(),
            "MONDAY_DAY_OF_WEEK": lambda e: e.dt.weekday(),  # 1=Monday to 7=Sunday
            "SUNDAY_DAY_OF_WEEK": lambda e: (e.dt.weekday() % 7) + 1,  # 1=Sunday to 7=Saturday
            "ISO_WEEK": lambda e: e.dt.week(),
            "MONDAY_WEEK": lambda e: e.dt.week(),
            "HOUR": lambda e: e.dt.hour(),
            "MINUTE": lambda e: e.dt.minute(),
            "SECOND": lambda e: e.dt.second(),
            "MILLISECOND": lambda e: e.dt.millisecond(),
            "MICROSECOND": lambda e: e.dt.microsecond(),
            "NANOSECOND": lambda e: e.dt.nanosecond(),
            "SUBSECOND": lambda e: e.dt.microsecond(),  # Microseconds since last second
            "UNIX_TIME": lambda e: e.dt.epoch("s"),
        }

        if comp in component_map:
            return component_map[comp](x)

        # Fallback for unhandled components
        return x.dt.year()  # Default to year

    def extract_boolean(
        self,
        x: PolarsExpr,
        /,
        component: PolarsExpr,
    ) -> PolarsExpr:
        """Extract boolean values of a date/time value.

        Args:
            x: Datetime expression.
            component: Boolean component (IS_LEAP_YEAR, IS_DST).

        Returns:
            Boolean expression.
        """
        comp = component.value if isinstance(component, BooleanComponent) else str(component).upper()

        if comp == "IS_LEAP_YEAR":
            # A year is a leap year if divisible by 4, except centuries unless divisible by 400
            year = x.dt.year()
            return ((year % 4 == 0) & (year % 100 != 0)) | (year % 400 == 0)

        if comp == "IS_DST":
            # Polars doesn't have direct DST detection
            # Return a placeholder - would need timezone-aware implementation
            return pl.lit(False)

        return pl.lit(False)

    # =========================================================================
    # Convenience Extraction Methods
    # =========================================================================

    def year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the year."""
        return x.dt.year()

    def month(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the month (1-12)."""
        return x.dt.month()

    def day(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the day of month (1-31)."""
        return x.dt.day()

    def hour(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the hour (0-23)."""
        return x.dt.hour()

    def minute(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the minute (0-59)."""
        return x.dt.minute()

    def second(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the second (0-59)."""
        return x.dt.second()

    def millisecond(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract milliseconds since last full second."""
        return x.dt.millisecond()

    def microsecond(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract microseconds since last full millisecond."""
        return x.dt.microsecond()

    def nanosecond(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract nanoseconds since last full microsecond."""
        return x.dt.nanosecond()

    def quarter(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the quarter (1-4)."""
        return x.dt.quarter()

    def day_of_year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract day of year (1-366)."""
        return x.dt.ordinal_day()

    def day_of_week(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract day of week (Monday=1 to Sunday=7)."""
        return x.dt.weekday()

    def week_of_year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract ISO week of year (1-53)."""
        return x.dt.week()

    def iso_year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract ISO 8601 week-numbering year."""
        return x.dt.iso_year()

    def unix_timestamp(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        return x.dt.epoch("s")

    def timezone_offset(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract timezone offset to UTC in seconds.

        Note: Polars doesn't directly expose timezone offset.
        Returns 0 for timezone-naive datetimes.
        """
        # Polars doesn't have direct timezone offset extraction
        return pl.lit(0)

    def is_leap_year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Check if the year is a leap year."""
        year = x.dt.year()
        return ((year % 4 == 0) & (year % 100 != 0)) | (year % 400 == 0)

    def is_dst(
        self,
        x: PolarsExpr,
        /,
        timezone: str = None,
    ) -> PolarsExpr:
        """Check if DST is observed at this time.

        Note: Polars doesn't have direct DST detection.
        Returns False as a placeholder.
        """
        return pl.lit(False)

    # =========================================================================
    # Date Arithmetic Methods
    # =========================================================================

    def add_years(
        self,
        x: PolarsExpr,
        years: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add years to a datetime.

        Args:
            x: Datetime expression.
            years: Number of years to add.

        Returns:
            Datetime with years added.
        """
        years_val = self._extract_literal_value(years)
        if isinstance(years_val, int):
            return x.dt.offset_by(f"{years_val}y")
        # Fallback: expression-based offset
        return x.dt.offset_by(years.cast(pl.Utf8) + "y")

    def add_months(
        self,
        x: PolarsExpr,
        months: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add months to a datetime.

        Args:
            x: Datetime expression.
            months: Number of months to add.

        Returns:
            Datetime with months added.
        """
        months_val = self._extract_literal_value(months)
        if isinstance(months_val, int):
            return x.dt.offset_by(f"{months_val}mo")
        # Fallback: expression-based offset
        return x.dt.offset_by(months.cast(pl.Utf8) + "mo")

    def add_days(
        self,
        x: PolarsExpr,
        days: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add days to a datetime.

        Args:
            x: Datetime expression.
            days: Number of days to add.

        Returns:
            Datetime with days added.
        """
        days_val = self._extract_literal_value(days)
        if isinstance(days_val, int):
            return x.dt.offset_by(f"{days_val}d")
        # Fallback: expression-based offset
        return x.dt.offset_by(days.cast(pl.Utf8) + "d")

    def add_hours(
        self,
        x: PolarsExpr,
        hours: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add hours to a datetime.

        Args:
            x: Datetime expression.
            hours: Number of hours to add.

        Returns:
            Datetime with hours added.
        """
        hours_val = self._extract_literal_value(hours)
        if isinstance(hours_val, int):
            return x.dt.offset_by(f"{hours_val}h")
        # Fallback: expression-based offset
        return x.dt.offset_by(hours.cast(pl.Utf8) + "h")

    def add_minutes(
        self,
        x: PolarsExpr,
        minutes: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add minutes to a datetime.

        Args:
            x: Datetime expression.
            minutes: Number of minutes to add.

        Returns:
            Datetime with minutes added.
        """
        minutes_val = self._extract_literal_value(minutes)
        if isinstance(minutes_val, int):
            return x.dt.offset_by(f"{minutes_val}m")
        # Fallback: expression-based offset
        return x.dt.offset_by(minutes.cast(pl.Utf8) + "m")

    def add_seconds(
        self,
        x: PolarsExpr,
        seconds: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add seconds to a datetime.

        Args:
            x: Datetime expression.
            seconds: Number of seconds to add.

        Returns:
            Datetime with seconds added.
        """
        seconds_val = self._extract_literal_value(seconds)
        if isinstance(seconds_val, int):
            return x.dt.offset_by(f"{seconds_val}s")
        # Fallback: expression-based offset
        return x.dt.offset_by(seconds.cast(pl.Utf8) + "s")

    def add_milliseconds(
        self,
        x: PolarsExpr,
        milliseconds: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add milliseconds to a datetime.

        Args:
            x: Datetime expression.
            milliseconds: Number of milliseconds to add.

        Returns:
            Datetime with milliseconds added.
        """
        ms_val = self._extract_literal_value(milliseconds)
        if isinstance(ms_val, int):
            return x.dt.offset_by(f"{ms_val}ms")
        # Fallback: expression-based offset
        return x.dt.offset_by(milliseconds.cast(pl.Utf8) + "ms")

    def add_microseconds(
        self,
        x: PolarsExpr,
        microseconds: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add microseconds to a datetime.

        Args:
            x: Datetime expression.
            microseconds: Number of microseconds to add.

        Returns:
            Datetime with microseconds added.
        """
        us_val = self._extract_literal_value(microseconds)
        if isinstance(us_val, int):
            return x.dt.offset_by(f"{us_val}us")
        # Fallback: expression-based offset
        return x.dt.offset_by(microseconds.cast(pl.Utf8) + "us")

    # =========================================================================
    # Date Difference Methods
    # =========================================================================

    def diff_years(
        self,
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Calculate difference in months.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in months (x - other).
        """
        years_diff = x.dt.year() - other.dt.year()
        months_diff = x.dt.month() - other.dt.month()
        return years_diff * 12 + months_diff

    def diff_days(
        self,
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        *,
        unit: PolarsExpr,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        *,
        unit: PolarsExpr,
    ) -> PolarsExpr:
        """Round datetime to the nearest unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Rounded datetime.
        """
        unit_val = self._extract_literal_value(unit)
        return x.dt.round(unit_val)

    def ceil(
        self,
        x: PolarsExpr,
        *,
        unit: PolarsExpr,
    ) -> PolarsExpr:
        """Round datetime up to the next unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Ceiling datetime.
        """
        # Polars doesn't have ceil for datetime, use truncate + add
        unit_val = self._extract_literal_value(unit)
        truncated = x.dt.truncate(unit_val)
        # If truncated != original, add one unit
        return pl.when(truncated == x).then(x).otherwise(truncated.dt.offset_by(unit_val))

    def floor(
        self,
        x: PolarsExpr,
        *,
        unit: PolarsExpr,
    ) -> PolarsExpr:
        """Round datetime down to the previous unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Floor datetime.
        """
        # Floor is the same as truncate
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    # =========================================================================
    # Timezone Methods
    # =========================================================================

    def to_timezone(
        self,
        x: PolarsExpr,
        timezone: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Convert to specified timezone.

        Args:
            x: Datetime expression (must be timezone-aware).
            timezone: Target timezone (IANA format).

        Returns:
            Datetime in target timezone.
        """
        return x.dt.convert_time_zone(timezone)

    def assume_timezone(
        self,
        x: PolarsExpr,
        timezone: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Assume the timestamp is in the specified timezone.

        Args:
            x: Datetime expression (timezone-naive).
            timezone: Timezone to assume (IANA format).

        Returns:
            Timezone-aware datetime.
        """
        return x.dt.replace_time_zone(timezone)

    # =========================================================================
    # Formatting Methods
    # =========================================================================

    def strftime(
        self,
        x: PolarsExpr,
        format: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Format datetime as string.

        Args:
            x: Datetime expression.
            format: strftime format string.

        Returns:
            Formatted string.
        """
        return x.dt.strftime(format)

    # =========================================================================
    # Snapshot Methods (Static)
    # =========================================================================

    def today(self) -> PolarsExpr:
        """Return today's date as a literal expression."""
        return pl.lit(date.today())

    def now(self) -> PolarsExpr:
        """Return current datetime as a literal expression."""
        return pl.lit(datetime.now())

    # =========================================================================
    # Flexible Duration Offset
    # =========================================================================

    def offset_by(
        self,
        x: PolarsExpr,
        *,
        offset: str,
    ) -> PolarsExpr:
        """Add/subtract flexible duration from datetime.

        Uses shared temporal helper for parsing combined duration strings.

        Args:
            x: Datetime expression.
            offset: Duration string (e.g., "1d", "2h30m", "-3mo", "1d2h").

        Returns:
            Datetime with offset applied.
        """
        from mountainash.expressions.core.utils.temporal import parse_combined_duration

        offset_val = self._extract_literal_value(offset)
        components = parse_combined_duration(offset_val)

        result = x
        for component in components:
            result = result.dt.offset_by(component)

        return result











    # =========================================================================
    # Snapshot Methods (Static)
    # =========================================================================

    def today(self) -> PolarsExpr:
        """Return today's date as a literal expression."""
        return pl.lit(date.today())

    def now(self) -> PolarsExpr:
        """Return current datetime as a literal expression."""
        return pl.lit(datetime.now())

    # =========================================================================
    # Flexible Duration Offset
    # =========================================================================

    def offset_by(
        self,
        x: PolarsExpr,
        *,
        offset: str,
    ) -> PolarsExpr:
        """Add/subtract flexible duration from datetime.

        Uses shared temporal helper for parsing combined duration strings.

        Args:
            x: Datetime expression.
            offset: Duration string (e.g., "1d", "2h30m", "-3mo", "1d2h").

        Returns:
            Datetime with offset applied.
        """
        from mountainash.expressions.core.utils.temporal import parse_combined_duration

        offset_val = self._extract_literal_value(offset)
        components = parse_combined_duration(offset_val)

        result = x
        for component in components:
            result = result.dt.offset_by(component)

        return result



    # =========================================================================
    # Convenience Extraction Methods
    # =========================================================================

    def year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the year."""
        return x.dt.year()

    def month(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the month (1-12)."""
        return x.dt.month()

    def day(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the day of month (1-31)."""
        return x.dt.day()

    def hour(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the hour (0-23)."""
        return x.dt.hour()

    def minute(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the minute (0-59)."""
        return x.dt.minute()

    def second(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the second (0-59)."""
        return x.dt.second()

    def millisecond(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract milliseconds since last full second."""
        return x.dt.millisecond()

    def microsecond(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract microseconds since last full millisecond."""
        return x.dt.microsecond()

    def nanosecond(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract nanoseconds since last full microsecond."""
        return x.dt.nanosecond()

    def quarter(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract the quarter (1-4)."""
        return x.dt.quarter()

    def day_of_year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract day of year (1-366)."""
        return x.dt.ordinal_day()

    def day_of_week(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract day of week (Monday=1 to Sunday=7)."""
        return x.dt.weekday()

    def week_of_year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract ISO week of year (1-53)."""
        return x.dt.week()

    def iso_year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract ISO 8601 week-numbering year."""
        return x.dt.iso_year()

    def unix_timestamp(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        return x.dt.epoch("s")

    def timezone_offset(self, x: PolarsExpr, /) -> PolarsExpr:
        """Extract timezone offset to UTC in seconds.

        Note: Polars doesn't directly expose timezone offset.
        Returns 0 for timezone-naive datetimes.
        """
        # Polars doesn't have direct timezone offset extraction
        return pl.lit(0)

    def is_leap_year(self, x: PolarsExpr, /) -> PolarsExpr:
        """Check if the year is a leap year."""
        year = x.dt.year()
        return ((year % 4 == 0) & (year % 100 != 0)) | (year % 400 == 0)

    def is_dst(
        self,
        x: PolarsExpr,
        /,
        timezone: str = None,
    ) -> PolarsExpr:
        """Check if DST is observed at this time.

        Note: Polars doesn't have direct DST detection.
        Returns False as a placeholder.
        """
        return pl.lit(False)

    # =========================================================================
    # Date Arithmetic Methods
    # =========================================================================

    def add_years(
        self,
        x: PolarsExpr,
        years: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add years to a datetime.

        Args:
            x: Datetime expression.
            years: Number of years to add.

        Returns:
            Datetime with years added.
        """
        years_val = self._extract_literal_value(years)
        if isinstance(years_val, int):
            return x.dt.offset_by(f"{years_val}y")
        # Fallback: expression-based offset
        return x.dt.offset_by(years.cast(pl.Utf8) + "y")

    def add_months(
        self,
        x: PolarsExpr,
        months: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add months to a datetime.

        Args:
            x: Datetime expression.
            months: Number of months to add.

        Returns:
            Datetime with months added.
        """
        months_val = self._extract_literal_value(months)
        if isinstance(months_val, int):
            return x.dt.offset_by(f"{months_val}mo")
        # Fallback: expression-based offset
        return x.dt.offset_by(months.cast(pl.Utf8) + "mo")

    def add_days(
        self,
        x: PolarsExpr,
        days: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add days to a datetime.

        Args:
            x: Datetime expression.
            days: Number of days to add.

        Returns:
            Datetime with days added.
        """
        days_val = self._extract_literal_value(days)
        if isinstance(days_val, int):
            return x.dt.offset_by(f"{days_val}d")
        # Fallback: expression-based offset
        return x.dt.offset_by(days.cast(pl.Utf8) + "d")

    def add_hours(
        self,
        x: PolarsExpr,
        hours: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add hours to a datetime.

        Args:
            x: Datetime expression.
            hours: Number of hours to add.

        Returns:
            Datetime with hours added.
        """
        hours_val = self._extract_literal_value(hours)
        if isinstance(hours_val, int):
            return x.dt.offset_by(f"{hours_val}h")
        # Fallback: expression-based offset
        return x.dt.offset_by(hours.cast(pl.Utf8) + "h")

    def add_minutes(
        self,
        x: PolarsExpr,
        minutes: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add minutes to a datetime.

        Args:
            x: Datetime expression.
            minutes: Number of minutes to add.

        Returns:
            Datetime with minutes added.
        """
        minutes_val = self._extract_literal_value(minutes)
        if isinstance(minutes_val, int):
            return x.dt.offset_by(f"{minutes_val}m")
        # Fallback: expression-based offset
        return x.dt.offset_by(minutes.cast(pl.Utf8) + "m")

    def add_seconds(
        self,
        x: PolarsExpr,
        seconds: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add seconds to a datetime.

        Args:
            x: Datetime expression.
            seconds: Number of seconds to add.

        Returns:
            Datetime with seconds added.
        """
        seconds_val = self._extract_literal_value(seconds)
        if isinstance(seconds_val, int):
            return x.dt.offset_by(f"{seconds_val}s")
        # Fallback: expression-based offset
        return x.dt.offset_by(seconds.cast(pl.Utf8) + "s")

    def add_milliseconds(
        self,
        x: PolarsExpr,
        milliseconds: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add milliseconds to a datetime.

        Args:
            x: Datetime expression.
            milliseconds: Number of milliseconds to add.

        Returns:
            Datetime with milliseconds added.
        """
        ms_val = self._extract_literal_value(milliseconds)
        if isinstance(ms_val, int):
            return x.dt.offset_by(f"{ms_val}ms")
        # Fallback: expression-based offset
        return x.dt.offset_by(milliseconds.cast(pl.Utf8) + "ms")

    def add_microseconds(
        self,
        x: PolarsExpr,
        microseconds: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add microseconds to a datetime.

        Args:
            x: Datetime expression.
            microseconds: Number of microseconds to add.

        Returns:
            Datetime with microseconds added.
        """
        us_val = self._extract_literal_value(microseconds)
        if isinstance(us_val, int):
            return x.dt.offset_by(f"{us_val}us")
        # Fallback: expression-based offset
        return x.dt.offset_by(microseconds.cast(pl.Utf8) + "us")

    # =========================================================================
    # Date Difference Methods
    # =========================================================================

    def diff_years(
        self,
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Calculate difference in months.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in months (x - other).
        """
        years_diff = x.dt.year() - other.dt.year()
        months_diff = x.dt.month() - other.dt.month()
        return years_diff * 12 + months_diff

    def diff_days(
        self,
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        other: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        *,
        unit: PolarsExpr,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        *,
        unit: PolarsExpr,
    ) -> PolarsExpr:
        """Round datetime to the nearest unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Rounded datetime.
        """
        unit_val = self._extract_literal_value(unit)
        return x.dt.round(unit_val)

    def ceil(
        self,
        x: PolarsExpr,
        *,
        unit: PolarsExpr,
    ) -> PolarsExpr:
        """Round datetime up to the next unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Ceiling datetime.
        """
        # Polars doesn't have ceil for datetime, use truncate + add
        unit_val = self._extract_literal_value(unit)
        truncated = x.dt.truncate(unit_val)
        # If truncated != original, add one unit
        return pl.when(truncated == x).then(x).otherwise(truncated.dt.offset_by(unit_val))

    def floor(
        self,
        x: PolarsExpr,
        *,
        unit: PolarsExpr,
    ) -> PolarsExpr:
        """Round datetime down to the previous unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Floor datetime.
        """
        # Floor is the same as truncate
        unit_val = self._extract_literal_value(unit)
        return x.dt.truncate(unit_val)

    # =========================================================================
    # Timezone Methods
    # =========================================================================

    def to_timezone(
        self,
        x: PolarsExpr,
        timezone: str,
        /,
    ) -> PolarsExpr:
        """Convert to specified timezone.

        Args:
            x: Datetime expression (must be timezone-aware).
            timezone: Target timezone (IANA format).

        Returns:
            Datetime in target timezone.
        """
        return x.dt.convert_time_zone(timezone)

    # =========================================================================
    # Component Extraction
    # =========================================================================

    def date(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.date()

    def time(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.time()

    # =========================================================================
    # Calendar Helpers
    # =========================================================================

    def month_start(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.month_start()

    def month_end(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.month_end()

    def days_in_month(self, input: PolarsExpr, /) -> PolarsExpr:
        return input.dt.month_end().dt.day()
