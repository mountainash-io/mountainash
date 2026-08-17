"""Ibis ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Ibis backend.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME,
)
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarDatetimeExpressionSystemProtocol
if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr, IbisTemporalExpr

_TO_TIMEZONE_UNSUPPORTED = (
    "to_timezone is not supported on ibis — the target zone never reaches the "
    "engine; see capabilities/datetime/value_classes_ma.py"
)
_IS_DST_UNSUPPORTED = (
    "is_dst is not supported on ibis — ibis has no DST/timezone-offset "
    "primitive; see capabilities/datetime/value_classes_ma.py"
)




class MountainAshIbisScalarDatetimeExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarDatetimeExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of ScalarDatetimeExpressionProtocol.

    Implements core datetime methods:
    - extract: Extract datetime components
    - extract_boolean: Extract boolean datetime properties

    Plus convenience methods for common operations.
    """

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
        timezone: str,
    ) -> IbisValueExpr:
        """Ibis has no timezone/DST detection primitive; declared UNSUPPORTED.

        Declared UNSUPPORTED on ibis (see capabilities/datetime/value_classes_ma.py)
        — the capability gate raises before this method is reached. The raise
        here is defence in depth (mirrors to_timezone's established pattern).
        """
        raise BackendCapabilityError(
            _IS_DST_UNSUPPORTED,
            backend="ibis",
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST,
        )

    # =========================================================================
    # Date Arithmetic Methods
    # =========================================================================

    def add_years(
        self,
        x: IbisTemporalExpr,
        years: IbisValueExpr | int,
        /,
    ) -> IbisValueExpr:
        """Add years to a datetime.

        Args:
            x: Datetime expression.
            years: Number of years to add.

        Returns:
            Datetime with years added.
        """
        return x + ibis.interval(years=int(years))

    def add_months(
        self,
        x: IbisTemporalExpr,
        months: IbisValueExpr | int,
        /,
    ) -> IbisValueExpr:
        """Add months to a datetime.

        Args:
            x: Datetime expression.
            months: Number of months to add.

        Returns:
            Datetime with months added.
        """
        return x + ibis.interval(months=int(months))

    def add_days(
        self,
        x: IbisTemporalExpr,
        days: IbisValueExpr | int,
        /,
    ) -> IbisValueExpr:
        """Add days to a datetime.

        Args:
            x: Datetime expression.
            days: Number of days to add.

        Returns:
            Datetime with days added.
        """
        return x + ibis.interval(days=int(days))

    def add_hours(
        self,
        x: IbisTemporalExpr,
        hours: IbisValueExpr | int,
        /,
    ) -> IbisValueExpr:
        """Add hours to a datetime.

        Args:
            x: Datetime expression.
            hours: Number of hours to add.

        Returns:
            Datetime with hours added.
        """
        return x + ibis.interval(hours=int(hours))

    def add_minutes(
        self,
        x: IbisTemporalExpr,
        minutes: IbisValueExpr | int,
        /,
    ) -> IbisValueExpr:
        """Add minutes to a datetime.

        Args:
            x: Datetime expression.
            minutes: Number of minutes to add.

        Returns:
            Datetime with minutes added.
        """
        return x + ibis.interval(minutes=int(minutes))

    def add_seconds(
        self,
        x: IbisTemporalExpr,
        seconds: IbisValueExpr | int,
        /,
    ) -> IbisValueExpr:
        """Add seconds to a datetime.

        Args:
            x: Datetime expression.
            seconds: Number of seconds to add.

        Returns:
            Datetime with seconds added.
        """
        return x + ibis.interval(seconds=int(seconds))

    def add_milliseconds(
        self,
        x: IbisTemporalExpr,
        milliseconds: IbisValueExpr | int,
        /,
    ) -> IbisValueExpr:
        """Add milliseconds to a datetime.

        Args:
            x: Datetime expression.
            milliseconds: Number of milliseconds to add.

        Returns:
            Datetime with milliseconds added.
        """
        return x + ibis.interval(milliseconds=int(milliseconds))

    def add_microseconds(
        self,
        x: IbisTemporalExpr,
        microseconds: IbisValueExpr | int,
        /,
    ) -> IbisValueExpr:
        """Add microseconds to a datetime.

        Args:
            x: Datetime expression.
            microseconds: Number of microseconds to add.

        Returns:
            Datetime with microseconds added.
        """
        return x + ibis.interval(microseconds=int(microseconds))

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
        unit: str,
    ) -> IbisValueExpr:
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
        x: IbisTemporalExpr,
        *,
        unit: str,
    ) -> IbisValueExpr:
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
        x: IbisTemporalExpr,
        *,
        unit: str,
    ) -> IbisValueExpr:
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
        x: IbisTemporalExpr,
        *,
        unit: str,
    ) -> IbisValueExpr:
        """Round datetime down to the previous unit.

        Args:
            x: Datetime expression.
            unit: Unit string (1d, 1h, 1mo, 1y, etc.).

        Returns:
            Floor datetime.
        """
        # Floor is the same as truncate.
        return self._round(x, "FLOOR", unit)

    def _round(self, x: IbisTemporalExpr, rounding: str, unit: str) -> IbisValueExpr:
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
        x: IbisTemporalExpr,
        /,
        timezone: str,
    ) -> IbisValueExpr:
        """Convert to specified timezone.

        Declared UNSUPPORTED on ibis (see
        capabilities/datetime/value_classes_ma.py) -- the capability gate raises
        before this method is reached. The raise here is defence in depth.
        """
        raise BackendCapabilityError(
            _TO_TIMEZONE_UNSUPPORTED,
            backend="ibis",
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE,
        )

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

    def total_days(self, x, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_days() method. "
            "Use dt.diff_days() for integer-based extraction."
        )

    def total_hours(self, x, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_hours() method. "
            "Use dt.diff_hours() for integer-based extraction."
        )

    def total_nanoseconds(self, x, /):
        raise NotImplementedError(
            "Ibis IntervalValue has no total_nanoseconds() method. "
            "Use integer arithmetic on dt.diff_seconds() for sub-nanosecond extraction."
        )
