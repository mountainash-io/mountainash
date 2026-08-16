"""Polars ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Polars backend.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarDatetimeExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr

# Type alias for expression type


class MountainAshPolarsScalarDatetimeExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarDatetimeExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of ScalarDatetimeExpressionProtocol.

    Implements core datetime methods:
    - extract: Extract datetime components (20+ component types)
    - extract_boolean: Extract boolean datetime properties

    Plus convenience methods for common operations:
    - Date arithmetic: add_days, add_months, add_years, etc.
    - Date difference: diff_days, diff_months, diff_years, etc.
    - Truncation: truncate, round_dt, ceil_dt, floor_dt
    - Timezone: to_timezone, assume_timezone
    - Formatting: strftime
    """

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
        timezone: Optional[str] = None,
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
            years: Number of years to add (accepts expressions).

        Returns:
            Datetime with years added.
        """
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
            months: Number of months to add (accepts expressions).

        Returns:
            Datetime with months added.
        """
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
            days: Number of days to add (accepts expressions).

        Returns:
            Datetime with days added.
        """
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
            hours: Number of hours to add (accepts expressions).

        Returns:
            Datetime with hours added.
        """
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
            minutes: Number of minutes to add (accepts expressions).

        Returns:
            Datetime with minutes added.
        """
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
            seconds: Number of seconds to add (accepts expressions).

        Returns:
            Datetime with seconds added.
        """
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
            milliseconds: Number of milliseconds to add (accepts expressions).

        Returns:
            Datetime with milliseconds added.
        """
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
            microseconds: Number of microseconds to add (accepts expressions).

        Returns:
            Datetime with microseconds added.
        """
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
        unit: str,
    ) -> PolarsExpr:
        """Truncate datetime to the specified unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Truncated datetime.
        """
        return self._round(x, "FLOOR", unit)

    def round_dt(
        self,
        x: PolarsExpr,
        *,
        unit: str,
    ) -> PolarsExpr:
        """Round datetime to the nearest unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Rounded datetime.
        """
        return self._round(x, "ROUND_TIE_UP", unit)

    def ceil_dt(
        self,
        x: PolarsExpr,
        *,
        unit: str,
    ) -> PolarsExpr:
        """Round datetime up to the next unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Ceiling datetime.
        """
        return self._round(x, "CEIL", unit)

    def floor_dt(
        self,
        x: PolarsExpr,
        *,
        unit: str,
    ) -> PolarsExpr:
        """Round datetime down to the previous unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Floor datetime.
        """
        # Floor is the same as truncate.
        return self._round(x, "FLOOR", unit)

    def _round(self, x: PolarsExpr, rounding: str, unit: str) -> PolarsExpr:
        """Redirect through the real round_temporal/round_calendar
        implementation (item 74). `unit` is already normalize_unit()'d and
        validate_ma_option()'d by the builder before it reaches here."""
        from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash._ma_option_domains import parse_ma_unit

        multiple, canonical_unit, family = parse_ma_unit(unit)
        if family == "calendar":
            return self.round_calendar(
                x, rounding=rounding, unit=canonical_unit, multiple=multiple
            )
        return self.round_temporal(
            x, rounding=rounding, unit=canonical_unit, multiple=multiple
        )

    # =========================================================================
    # Timezone Methods
    # =========================================================================

    def to_timezone(
        self,
        x: PolarsExpr,
        /,
        timezone: str,
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

        components = parse_combined_duration(offset)

        result = x
        for component in components:
            result = result.dt.offset_by(component)

        return result




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

    # =========================================================================
    # Duration Extraction Methods
    # =========================================================================

    def total_seconds(self, x: PolarsExpr, /) -> PolarsExpr:
        return x.dt.total_seconds()

    def total_minutes(self, x: PolarsExpr, /) -> PolarsExpr:
        return x.dt.total_minutes()

    def total_milliseconds(self, x: PolarsExpr, /) -> PolarsExpr:
        return x.dt.total_milliseconds()

    def total_microseconds(self, x: PolarsExpr, /) -> PolarsExpr:
        return x.dt.total_microseconds()

    def total_days(self, x: PolarsExpr, /) -> PolarsExpr:
        return x.dt.total_days()

    def total_hours(self, x: PolarsExpr, /) -> PolarsExpr:
        return x.dt.total_hours()

    def total_nanoseconds(self, x: PolarsExpr, /) -> PolarsExpr:
        return x.dt.total_nanoseconds()
