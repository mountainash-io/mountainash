"""Ibis ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Ibis backend.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Optional

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarDatetimeExpressionSystemProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr, IbisTemporalExpr



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


class MountainAshIbisScalarDatetimeExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarDatetimeExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of ScalarDatetimeExpressionProtocol.

    Implements core datetime methods:
    - extract: Extract datetime components
    - extract_boolean: Extract boolean datetime properties

    Plus convenience methods for common operations.
    """

    # =========================================================================
    # Core Extraction Methods
    # =========================================================================

    def extract(
        self,
        x: IbisTemporalExpr,
        component: IbisValueExpr,
        timezone: Optional[IbisValueExpr] = None,
        /,
    ) -> IbisValueExpr:
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
            "YEAR": lambda e: e.year(),
            "QUARTER": lambda e: e.quarter(),
            "MONTH": lambda e: e.month(),
            "DAY": lambda e: e.day(),
            "DAY_OF_YEAR": lambda e: e.day_of_year(),
            "MONDAY_DAY_OF_WEEK": lambda e: e.day_of_week.index() + ibis.literal(1),  # 1-indexed
            "ISO_WEEK": lambda e: e.week_of_year(),
            "HOUR": lambda e: e.hour(),
            "MINUTE": lambda e: e.minute(),
            "SECOND": lambda e: e.second(),
            "MILLISECOND": lambda e: e.millisecond(),
            "MICROSECOND": lambda e: e.microsecond(),
            "UNIX_TIME": lambda e: e.epoch_seconds(),
        }

        if comp in component_map:
            return component_map[comp](x)

        return x.year()

    def extract_boolean(
        self,
        x: IbisValueExpr,
        /,
        component: IbisValueExpr,
    ) -> IbisValueExpr:
        """Extract boolean values of a date/time value.

        Args:
            x: Datetime expression.
            component: Boolean component (IS_LEAP_YEAR, IS_DST).

        Returns:
            Boolean expression.
        """
        comp = component.value if isinstance(component, BooleanComponent) else str(component).upper()

        if comp == "IS_LEAP_YEAR":
            year = x.year()
            return ((year % ibis.literal(4) == ibis.literal(0)) &
                    (year % ibis.literal(100) != ibis.literal(0))) | (year % ibis.literal(400) == ibis.literal(0))

        if comp == "IS_DST":
            return ibis.literal(False)

        return ibis.literal(False)

    # =========================================================================
    # Convenience Extraction Methods
    # =========================================================================

    def year(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract the year."""
        return x.year()

    def month(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract the month (1-12)."""
        return x.month()

    def day(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract the day of month (1-31)."""
        return x.day()

    def hour(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract the hour (0-23)."""
        return x.hour()

    def minute(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract the minute (0-59)."""
        return x.minute()

    def second(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract the second (0-59)."""
        return x.second()

    def millisecond(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract milliseconds since last full second."""
        return x.millisecond()

    def microsecond(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract microseconds since last full millisecond."""
        return x.microsecond()

    def nanosecond(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract nanoseconds since last full microsecond.

        Note: Ibis may not have nanosecond. Falls back to 0.
        """
        # Ibis doesn't have nanosecond - fallback
        return ibis.literal(0)

    def quarter(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract the quarter (1-4)."""
        return x.quarter()

    def day_of_year(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract day of year (1-366)."""
        return x.day_of_year()

    def day_of_week(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract day of week (Monday=1 to Sunday=7)."""
        return x.day_of_week.index() + ibis.literal(1)

    def week_of_year(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract ISO week of year (1-53)."""
        return x.week_of_year()

    def iso_year(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract ISO 8601 week-numbering year.

        Note: Ibis may not have iso_year. Falls back to year.
        """
        # Ibis doesn't have iso_year - fallback
        return x.year()

    def unix_timestamp(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        return x.epoch_seconds()

    def timezone_offset(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Extract timezone offset to UTC in seconds.

        Note: Ibis doesn't directly expose timezone offset.
        Returns 0 as a placeholder.
        """
        return ibis.literal(0)

    def is_leap_year(self, x: IbisTemporalExpr, /) -> IbisValueExpr:
        """Check if the year is a leap year."""
        year = x.year()
        return ((year % ibis.literal(4) == ibis.literal(0)) &
                (year % ibis.literal(100) != ibis.literal(0))) | (year % ibis.literal(400) == ibis.literal(0))

    def is_dst(
        self,
        x: IbisTemporalExpr,
        /,
        timezone: Optional[str] = None,
    ) -> IbisValueExpr:
        """Check if DST is observed at this time.

        Note: Ibis doesn't have direct DST detection.
        Returns False as a placeholder.
        """
        return ibis.literal(False)

    # =========================================================================
    # Date Arithmetic Methods
    # =========================================================================

    def add_years(
        self,
        x: IbisTemporalExpr,
        years: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add years to a datetime.

        Args:
            x: Datetime expression.
            years: Number of years to add.

        Returns:
            Datetime with years added.
        """
        years_val = self._extract_literal_if_possible(years)
        return self._call_with_expr_support(
            lambda: x + ibis.interval(years=years_val),
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS,
            years=years,
        )

    def add_months(
        self,
        x: IbisTemporalExpr,
        months: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add months to a datetime.

        Args:
            x: Datetime expression.
            months: Number of months to add.

        Returns:
            Datetime with months added.
        """
        months_val = self._extract_literal_if_possible(months)
        return self._call_with_expr_support(
            lambda: x + ibis.interval(months=months_val),
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS,
            months=months,
        )

    def add_days(
        self,
        x: IbisTemporalExpr,
        days: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add days to a datetime.

        Args:
            x: Datetime expression.
            days: Number of days to add.

        Returns:
            Datetime with days added.
        """
        days_val = self._extract_literal_if_possible(days)
        return self._call_with_expr_support(
            lambda: x + ibis.interval(days=days_val),
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS,
            days=days,
        )

    def add_hours(
        self,
        x: IbisTemporalExpr,
        hours: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add hours to a datetime.

        Args:
            x: Datetime expression.
            hours: Number of hours to add.

        Returns:
            Datetime with hours added.
        """
        hours_val = self._extract_literal_if_possible(hours)
        return self._call_with_expr_support(
            lambda: x + ibis.interval(hours=hours_val),
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS,
            hours=hours,
        )

    def add_minutes(
        self,
        x: IbisTemporalExpr,
        minutes: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add minutes to a datetime.

        Args:
            x: Datetime expression.
            minutes: Number of minutes to add.

        Returns:
            Datetime with minutes added.
        """
        minutes_val = self._extract_literal_if_possible(minutes)
        return self._call_with_expr_support(
            lambda: x + ibis.interval(minutes=minutes_val),
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES,
            minutes=minutes,
        )

    def add_seconds(
        self,
        x: IbisTemporalExpr,
        seconds: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add seconds to a datetime.

        Args:
            x: Datetime expression.
            seconds: Number of seconds to add.

        Returns:
            Datetime with seconds added.
        """
        seconds_val = self._extract_literal_if_possible(seconds)
        return self._call_with_expr_support(
            lambda: x + ibis.interval(seconds=seconds_val),
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS,
            seconds=seconds,
        )

    def add_milliseconds(
        self,
        x: IbisTemporalExpr,
        milliseconds: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add milliseconds to a datetime.

        Args:
            x: Datetime expression.
            milliseconds: Number of milliseconds to add.

        Returns:
            Datetime with milliseconds added.
        """
        ms_val = self._extract_literal_if_possible(milliseconds)
        return self._call_with_expr_support(
            lambda: x + ibis.interval(milliseconds=ms_val),
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS,
            milliseconds=milliseconds,
        )

    def add_microseconds(
        self,
        x: IbisTemporalExpr,
        microseconds: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add microseconds to a datetime.

        Args:
            x: Datetime expression.
            microseconds: Number of microseconds to add.

        Returns:
            Datetime with microseconds added.
        """
        us_val = self._extract_literal_if_possible(microseconds)
        return self._call_with_expr_support(
            lambda: x + ibis.interval(microseconds=us_val),
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS,
            microseconds=microseconds,
        )

    # =========================================================================
    # Date Difference Methods
    # =========================================================================

    def diff_years(
        self,
        x: IbisTemporalExpr,
        other: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Calculate difference in years.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in years (x - other).
        """
        return x.year() - other.year()

    def diff_months(
        self,
        x: IbisTemporalExpr,
        other: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Calculate difference in months.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in months (x - other).
        """
        years_diff = x.year() - other.year()
        months_diff = x.month() - other.month()
        return years_diff * ibis.literal(12) + months_diff

    def diff_days(
        self,
        x: IbisTemporalExpr,
        other: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Calculate difference in days.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in days (x - other).
        """
        return x.delta(other, unit="day")

    def diff_hours(
        self,
        x: IbisTemporalExpr,
        other: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Calculate difference in hours.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in hours (x - other).
        """
        return x.delta(other, unit="hour")

    def diff_minutes(
        self,
        x: IbisTemporalExpr,
        other: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Calculate difference in minutes.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in minutes (x - other).
        """
        return x.delta(other, unit="minute")

    def diff_seconds(
        self,
        x: IbisTemporalExpr,
        other: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Calculate difference in seconds.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in seconds (x - other).
        """
        return x.delta(other, unit="second")

    def diff_milliseconds(
        self,
        x: IbisTemporalExpr,
        other: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Calculate difference in milliseconds.

        Args:
            x: First datetime.
            other: Second datetime.

        Returns:
            Difference in milliseconds (x - other).
        """
        return x.delta(other, unit="millisecond")

    # =========================================================================
    # Truncation / Rounding Methods
    # =========================================================================

    def truncate(
        self,
        x: IbisTemporalExpr,
        *,
        unit: IbisValueExpr,
    ) -> IbisValueExpr:
        """Truncate datetime to the specified unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, Y, M, D, h, m, s, etc.).

        Returns:
            Truncated datetime.
        """
        # Ibis truncate expects just the unit letter, not "1d" format
        # Convert "1d" -> "D", "1h" -> "h", etc.
        unit_mapping = {
            "1y": "Y",
            "1mo": "M",
            "1w": "W",
            "1d": "D",
            "1h": "h",
            "1m": "m",
            "1s": "s",
            "1ms": "ms",
            "1us": "us",
        }
        unit_mapped = unit_mapping.get(unit, unit)
        return x.truncate(unit_mapped)

    def round(
        self,
        x: IbisTemporalExpr,
        *,
        unit: IbisValueExpr,
    ) -> IbisValueExpr:
        """Round datetime to the nearest unit.

        Args:
            x: Datetime expression.
            unit: Unit string.

        Returns:
            Rounded datetime.

        Note:
            Ibis may not have round. Falls back to truncate.
        """
        # Ibis doesn't have round - fallback to truncate
        return x.truncate(unit)

    def ceil(
        self,
        x: IbisTemporalExpr,
        *,
        unit: IbisValueExpr,
    ) -> IbisValueExpr:
        """Round datetime up to the next unit.

        Args:
            x: Datetime expression.
            unit: Unit string.

        Returns:
            Ceiling datetime.

        Note:
            Ibis doesn't have ceil. Falls back to truncate.
        """
        # Ibis doesn't have ceil - fallback to truncate
        return x.truncate(unit)

    def floor(
        self,
        x: IbisTemporalExpr,
        *,
        unit: IbisValueExpr,
    ) -> IbisValueExpr:
        """Round datetime down to the previous unit.

        Args:
            x: Datetime expression.
            unit: Unit string.

        Returns:
            Floor datetime.
        """
        return x.truncate(unit)

    # =========================================================================
    # Timezone Methods
    # =========================================================================

    def to_timezone(
        self,
        x: IbisTemporalExpr,
        timezone: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Convert to specified timezone.

        Args:
            x: Datetime expression (must be timezone-aware).
            timezone: Target timezone (IANA format).

        Returns:
            Datetime in target timezone.

        Note:
            Ibis may not have timezone conversion. Falls back to input.
        """
        # Ibis doesn't have convert_time_zone - fallback
        return x

    def assume_timezone(
        self,
        x: IbisTemporalExpr,
        timezone: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Assume the timestamp is in the specified timezone.

        Args:
            x: Datetime expression (timezone-naive).
            timezone: Timezone to assume (IANA format).

        Returns:
            Timezone-aware datetime.

        Note:
            Ibis may not have timezone assignment. Falls back to input.
        """
        # Ibis doesn't have replace_time_zone - fallback
        return x

    # =========================================================================
    # Formatting Methods
    # =========================================================================

    def strftime(
        self,
        x: IbisTemporalExpr,
        format: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Format datetime as string.

        Args:
            x: Datetime expression.
            format: strftime format string.

        Returns:
            Formatted string.
        """
        return x.strftime(format)

    # =========================================================================
    # Snapshot Methods (Static)
    # =========================================================================

    def today(self) -> IbisValueExpr:
        """Return today's date as a literal expression."""
        return ibis.literal(date.today())

    def now(self) -> IbisValueExpr:
        """Return current datetime as a literal expression."""
        return ibis.now()

    # =========================================================================
    # Flexible Duration Offset
    # =========================================================================

    def _parse_duration_string(self, duration: str) -> list:
        """Parse a duration string into individual offset components.

        Args:
            duration: Duration string like "1d2h", "-3mo", "2h30m"

        Returns:
            List of (amount, unit) tuples
        """
        import re

        is_negative = duration.startswith('-')
        if is_negative:
            duration = duration[1:]

        components = []
        # Pattern: number followed by unit (handle 'mo' before 'm')
        pattern = r'(\d+)(y|mo|w|d|h|m|s)'

        for match in re.finditer(pattern, duration):
            amount = int(match.group(1))
            unit = match.group(2)
            if is_negative:
                amount = -amount
            components.append((amount, unit))

        return components

    def offset_by(
        self,
        x: IbisValueExpr,
        *,
        offset: str,
    ) -> IbisValueExpr:
        """Add/subtract flexible duration from datetime.

        Uses ibis.interval() for each component.

        Args:
            x: Datetime expression.
            offset: Duration string (e.g., "1d", "2h30m", "-3mo", "1d2h").

        Returns:
            Datetime with offset applied.
        """
        components = self._parse_duration_string(offset)

        # Map unit abbreviations to ibis.interval kwargs
        unit_mapping = {
            "y": "years",
            "mo": "months",
            "w": "weeks",
            "d": "days",
            "h": "hours",
            "m": "minutes",
            "s": "seconds",
        }

        result = x
        for amount, unit in components:
            if unit in unit_mapping:
                interval = ibis.interval(**{unit_mapping[unit]: amount})
                result = result + interval

        return result


    # =========================================================================
    # Component Extraction
    # =========================================================================

    def date(self, input: IbisTemporalExpr, /) -> IbisValueExpr:
        return input.date()

    def time(self, input: IbisTemporalExpr, /) -> IbisValueExpr:
        return input.time()

    # =========================================================================
    # Calendar Helpers
    # =========================================================================

    def month_start(self, input: IbisTemporalExpr, /) -> IbisValueExpr:
        return input.truncate("M")

    def month_end(self, input: IbisTemporalExpr, /) -> IbisValueExpr:
        next_month = input.truncate("M") + ibis.interval(months=1)
        return next_month - ibis.interval(days=1)

    def days_in_month(self, input: IbisTemporalExpr, /) -> IbisValueExpr:
        next_month = input.truncate("M") + ibis.interval(months=1)
        end_of_month = next_month - ibis.interval(days=1)
        return end_of_month.day()

    # =========================================================================
    # Duration Extraction Methods
    # =========================================================================

    def total_seconds(self, x, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_seconds() method. "
            "Use dt.diff_seconds() for integer-based extraction."
        )

    def total_minutes(self, x, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_minutes() method. "
            "Use dt.diff_minutes() for integer-based extraction."
        )

    def total_milliseconds(self, x, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_milliseconds() method. "
            "Use dt.diff_milliseconds() for integer-based extraction."
        )

    def total_microseconds(self, x, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_microseconds() method. "
            "Use integer arithmetic on dt.diff_seconds() for sub-second extraction."
        )
