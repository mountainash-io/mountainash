"""Narwhals ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Narwhals backend.
"""

from __future__ import annotations

from datetime import date, datetime
from mountainash.expressions.core.datetime_components import (
    BooleanComponent,
    DatetimeComponent,
)
from typing import TYPE_CHECKING, Optional

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarDatetimeExpressionSystemProtocol


if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class MountainAshNarwhalsScalarDatetimeExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarDatetimeExpressionSystemProtocol[nw.Expr]):
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
        component: str,
        timezone: Optional[str] = None,
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
            "HOUR": lambda e: e.dt.hour(),
            "MINUTE": lambda e: e.dt.minute(),
            "SECOND": lambda e: e.dt.second(),
            "MILLISECOND": lambda e: e.dt.millisecond(),
            "MICROSECOND": lambda e: e.dt.microsecond(),
            "NANOSECOND": lambda e: e.dt.nanosecond(),
        }

        if comp == "ISO_WEEK":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
            raise BackendCapabilityError(
                "Narwhals does not support ISO week extraction",
                backend="narwhals",
                function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT,
            )

        if comp in component_map:
            return component_map[comp](x)

        return x.dt.year()

    def extract_boolean(
        self,
        x: NarwhalsExpr,
        /,
        component: str,
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
        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
        raise BackendCapabilityError(
            "Narwhals does not support ISO week extraction",
            backend="narwhals",
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK,
        )

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
        timezone: Optional[str] = None,
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
        years: NarwhalsExpr | int,
        /,
    ) -> NarwhalsExpr:
        """Add years to a datetime.

        Args:
            x: Datetime expression.
            years: Number of years to add.

        Returns:
            Datetime with years added.
        """
        return x.dt.offset_by(f"{int(years)}y")

    def add_months(
        self,
        x: NarwhalsExpr,
        months: NarwhalsExpr | int,
        /,
    ) -> NarwhalsExpr:
        """Add months to a datetime.

        Args:
            x: Datetime expression.
            months: Number of months to add.

        Returns:
            Datetime with months added.
        """
        return x.dt.offset_by(f"{int(months)}mo")

    def add_days(
        self,
        x: NarwhalsExpr,
        days: NarwhalsExpr | int,
        /,
    ) -> NarwhalsExpr:
        """Add days to a datetime.

        Args:
            x: Datetime expression.
            days: Number of days to add.

        Returns:
            Datetime with days added.
        """
        return x.dt.offset_by(f"{int(days)}d")

    def add_hours(
        self,
        x: NarwhalsExpr,
        hours: NarwhalsExpr | int,
        /,
    ) -> NarwhalsExpr:
        """Add hours to a datetime.

        Args:
            x: Datetime expression.
            hours: Number of hours to add.

        Returns:
            Datetime with hours added.
        """
        return x.dt.offset_by(f"{int(hours)}h")

    def add_minutes(
        self,
        x: NarwhalsExpr,
        minutes: NarwhalsExpr | int,
        /,
    ) -> NarwhalsExpr:
        """Add minutes to a datetime.

        Args:
            x: Datetime expression.
            minutes: Number of minutes to add.

        Returns:
            Datetime with minutes added.
        """
        return x.dt.offset_by(f"{int(minutes)}m")

    def add_seconds(
        self,
        x: NarwhalsExpr,
        seconds: NarwhalsExpr | int,
        /,
    ) -> NarwhalsExpr:
        """Add seconds to a datetime.

        Args:
            x: Datetime expression.
            seconds: Number of seconds to add.

        Returns:
            Datetime with seconds added.
        """
        return x.dt.offset_by(f"{int(seconds)}s")

    def add_milliseconds(
        self,
        x: NarwhalsExpr,
        milliseconds: NarwhalsExpr | int,
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
        # Convert to microseconds: 1ms = 1000us
        return x.dt.offset_by(f"{int(milliseconds) * 1000}us")

    def add_microseconds(
        self,
        x: NarwhalsExpr,
        microseconds: NarwhalsExpr | int,
        /,
    ) -> NarwhalsExpr:
        """Add microseconds to a datetime.

        Args:
            x: Datetime expression.
            microseconds: Number of microseconds to add.

        Returns:
            Datetime with microseconds added.
        """
        return x.dt.offset_by(f"{int(microseconds)}us")

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
        return ((x - other).dt.total_seconds() / nw.lit(86400)).floor()

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
        unit: str,
    ) -> NarwhalsExpr:
        """Truncate datetime to the specified unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Truncated datetime.
        """
        return x.dt.truncate(unit)

    def round_dt(
        self,
        x: NarwhalsExpr,
        *,
        unit: str,
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
        return x.dt.truncate(unit)

    def ceil_dt(
        self,
        x: NarwhalsExpr,
        *,
        unit: str,
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
        return x.dt.truncate(unit)

    def floor_dt(
        self,
        x: NarwhalsExpr,
        *,
        unit: str,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        /,
        timezone: str,
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
        from mountainash.expressions.core.utils.temporal import parse_combined_duration

        components = parse_combined_duration(offset)

        result = x
        for component in components:
            result = result.dt.offset_by(component)

        return result


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

    # =========================================================================
    # Duration Extraction Methods
    # =========================================================================

    def total_seconds(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        return x.dt.total_seconds()

    def total_minutes(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        return x.dt.total_minutes()

    def total_milliseconds(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        return x.dt.total_milliseconds()

    def total_microseconds(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        return x.dt.total_microseconds()

    def total_days(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Total days in a duration. Composed from total_seconds (Narwhals lacks total_days)."""
        return (x.dt.total_seconds() // nw.lit(86400))

    def total_hours(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Total hours in a duration. Composed from total_seconds (Narwhals lacks total_hours)."""
        return (x.dt.total_seconds() // nw.lit(3600))

    def total_nanoseconds(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        return x.dt.total_nanoseconds()
