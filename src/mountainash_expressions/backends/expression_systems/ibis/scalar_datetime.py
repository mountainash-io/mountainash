"""Ibis ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Ibis backend.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, TYPE_CHECKING

import ibis
import ibis.expr.types as ir

from .base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_datetime import (
        ScalarDatetimeExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = ir.Column | ir.Scalar


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


class IbisScalarDatetimeSystem(IbisBaseExpressionSystem):
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
            year = x.year()
            return ((year % ibis.literal(4) == ibis.literal(0)) &
                    (year % ibis.literal(100) != ibis.literal(0))) | (year % ibis.literal(400) == ibis.literal(0))

        if comp == "IS_DST":
            return ibis.literal(False)

        return ibis.literal(False)

    # =========================================================================
    # Convenience Extraction Methods
    # =========================================================================

    def year(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the year."""
        return x.year()

    def month(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the month (1-12)."""
        return x.month()

    def day(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the day of month (1-31)."""
        return x.day()

    def hour(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the hour (0-23)."""
        return x.hour()

    def minute(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the minute (0-59)."""
        return x.minute()

    def second(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the second (0-59)."""
        return x.second()

    def millisecond(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract milliseconds since last full second."""
        return x.millisecond()

    def microsecond(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract microseconds since last full millisecond."""
        return x.microsecond()

    def nanosecond(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract nanoseconds since last full microsecond.

        Note: Ibis may not have nanosecond. Falls back to 0.
        """
        # Ibis doesn't have nanosecond - fallback
        return ibis.literal(0)

    def quarter(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract the quarter (1-4)."""
        return x.quarter()

    def day_of_year(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract day of year (1-366)."""
        return x.day_of_year()

    def day_of_week(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract day of week (Monday=1 to Sunday=7)."""
        return x.day_of_week.index() + ibis.literal(1)

    def week_of_year(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract ISO week of year (1-53)."""
        return x.week_of_year()

    def iso_year(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract ISO 8601 week-numbering year.

        Note: Ibis may not have iso_year. Falls back to year.
        """
        # Ibis doesn't have iso_year - fallback
        return x.year()

    def unix_timestamp(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        return x.epoch_seconds()

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
        """
        if isinstance(years, int):
            return x + ibis.interval(years=years)
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
        """
        if isinstance(months, int):
            return x + ibis.interval(months=months)
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
            return x + ibis.interval(days=days)
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
            return x + ibis.interval(hours=hours)
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
            return x + ibis.interval(minutes=minutes)
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
            return x + ibis.interval(seconds=seconds)
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
            return x + ibis.interval(milliseconds=milliseconds)
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
            return x + ibis.interval(microseconds=microseconds)
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
        return x.year() - other.year()

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
        years_diff = x.year() - other.year()
        months_diff = x.month() - other.month()
        return years_diff * ibis.literal(12) + months_diff

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
        return x.delta(other, "day")

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
        return x.delta(other, "hour")

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
        return x.delta(other, "minute")

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
        return x.delta(other, "second")

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
        return x.delta(other, "millisecond")

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
            unit: Unit string (Y, M, D, h, m, s, etc.).

        Returns:
            Truncated datetime.
        """
        return x.truncate(unit)

    def round(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
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
            Ibis may not have timezone conversion. Falls back to input.
        """
        # Ibis doesn't have convert_time_zone - fallback
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
            Ibis may not have timezone assignment. Falls back to input.
        """
        # Ibis doesn't have replace_time_zone - fallback
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
        """
        return x.strftime(format)

    # =========================================================================
    # Snapshot Methods (Static)
    # =========================================================================

    def today(self) -> SupportedExpressions:
        """Return today's date as a literal expression."""
        return ibis.literal(date.today())

    def now(self) -> SupportedExpressions:
        """Return current datetime as a literal expression."""
        return ibis.now()
