"""Polars temporal operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import TemporalExpressionProtocol


class PolarsTemporalExpressionSystem(PolarsBaseExpressionSystem, TemporalExpressionProtocol):
    """
    Polars implementation of temporal/datetime operations.

    Implements TemporalExpressionProtocol methods.

    Note:
        RENAMED: All methods changed from temporal_* to dt_* prefix to match protocol.
        Deprecated backend used temporal_year(), protocol expects dt_year(), etc.
    """

    # ========================================
    # Temporal Extraction Operations
    # ========================================

    def dt_year(self, operand: Any) -> pl.Expr:
        """Extract year from datetime using Polars dt.year()."""
        return operand.dt.year()

    def dt_month(self, operand: Any) -> pl.Expr:
        """Extract month from datetime using Polars dt.month()."""
        return operand.dt.month()

    def dt_day(self, operand: Any) -> pl.Expr:
        """Extract day from datetime using Polars dt.day()."""
        return operand.dt.day()

    def dt_hour(self, operand: Any) -> pl.Expr:
        """Extract hour from datetime using Polars dt.hour()."""
        return operand.dt.hour()

    def dt_minute(self, operand: Any) -> pl.Expr:
        """Extract minute from datetime using Polars dt.minute()."""
        return operand.dt.minute()

    def dt_second(self, operand: Any) -> pl.Expr:
        """Extract second from datetime using Polars dt.second()."""
        return operand.dt.second()

    def dt_weekday(self, operand: Any) -> pl.Expr:
        """
        Extract day of week from datetime (0=Monday, 6=Sunday).

        Returns:
            pl.Expr with weekday as 0-6 (Monday-Sunday)

        Note:
            Polars dt.weekday() returns ISO weekday (1=Monday, 7=Sunday).
            We convert to 0-6 to match Python's convention.
        """
        return operand.dt.weekday() - 1

    def dt_week(self, operand: Any) -> pl.Expr:
        """Extract week number from datetime using Polars dt.week()."""
        return operand.dt.week()

    def dt_quarter(self, operand: Any) -> pl.Expr:
        """Extract quarter from datetime using Polars dt.quarter()."""
        return operand.dt.quarter()

    # ========================================
    # Temporal Addition Operations
    # ========================================

    def dt_add_days(self, operand: Any, days: Any) -> pl.Expr:
        """
        Add days to a date using Polars dt.offset_by().

        Args:
            operand: Date/datetime expression
            days: Number of days to add (can be expression or literal)

        Returns:
            pl.Expr with days added
        """
        # Convert raw values to Polars expressions
        days_expr = pl.lit(days) if not isinstance(days, pl.Expr) else days
        return operand.dt.offset_by(days_expr.cast(pl.Utf8) + pl.lit("d"))

    def dt_add_months(self, operand: Any, months: Any) -> pl.Expr:
        """
        Add months to a date using Polars dt.offset_by().

        Args:
            operand: Date/datetime expression
            months: Number of months to add (can be expression or literal)

        Returns:
            pl.Expr with months added
        """
        # Convert raw values to Polars expressions
        months_expr = pl.lit(months) if not isinstance(months, pl.Expr) else months
        return operand.dt.offset_by(months_expr.cast(pl.Utf8) + pl.lit("mo"))

    def dt_add_years(self, operand: Any, years: Any) -> pl.Expr:
        """
        Add years to a date using Polars dt.offset_by().

        Args:
            operand: Date/datetime expression
            years: Number of years to add (can be expression or literal)

        Returns:
            pl.Expr with years added
        """
        # Convert raw values to Polars expressions
        years_expr = pl.lit(years) if not isinstance(years, pl.Expr) else years
        return operand.dt.offset_by(years_expr.cast(pl.Utf8) + pl.lit("y"))

    def dt_add_hours(self, operand: Any, hours: Any) -> pl.Expr:
        """
        Add hours to a datetime using Polars dt.offset_by().

        Args:
            operand: Datetime expression
            hours: Number of hours to add (can be expression or literal)

        Returns:
            pl.Expr with hours added
        """
        # Convert raw values to Polars expressions
        hours_expr = pl.lit(hours) if not isinstance(hours, pl.Expr) else hours
        return operand.dt.offset_by(hours_expr.cast(pl.Utf8) + pl.lit("h"))

    def dt_add_minutes(self, operand: Any, minutes: Any) -> pl.Expr:
        """
        Add minutes to a datetime using Polars dt.offset_by().

        Args:
            operand: Datetime expression
            minutes: Number of minutes to add (can be expression or literal)

        Returns:
            pl.Expr with minutes added
        """
        # Convert raw values to Polars expressions
        minutes_expr = pl.lit(minutes) if not isinstance(minutes, pl.Expr) else minutes
        return operand.dt.offset_by(minutes_expr.cast(pl.Utf8) + pl.lit("m"))

    def dt_add_seconds(self, operand: Any, seconds: Any) -> pl.Expr:
        """
        Add seconds to a datetime using Polars dt.offset_by().

        Args:
            operand: Datetime expression
            seconds: Number of seconds to add (can be expression or literal)

        Returns:
            pl.Expr with seconds added
        """
        # Convert raw values to Polars expressions
        seconds_expr = pl.lit(seconds) if not isinstance(seconds, pl.Expr) else seconds
        return operand.dt.offset_by(seconds_expr.cast(pl.Utf8) + pl.lit("s"))

    # ========================================
    # Temporal Difference Operations
    # ========================================

    def dt_diff_years(self, operand: Any, other_date: Any) -> pl.Expr:
        """
        Calculate difference in years between two dates.

        Args:
            operand: First date
            other_date: Second date

        Returns:
            pl.Expr with year difference (operand - other_date)
        """
        return operand.dt.year() - other.dt.year()

    def dt_diff_months(self, operand: Any, other_date: Any) -> pl.Expr:
        """
        Calculate difference in months between two dates.

        Args:
            operand: First date
            other_date: Second date

        Returns:
            pl.Expr with month difference (operand - other_date)

        Note:
            This is an approximate calculation based on year*12 + month.
        """
        years_diff = operand.dt.year() - other_date.dt.year()
        months_diff = operand.dt.month() - other_date.dt.month()
        return years_diff * 12 + months_diff

    def dt_diff_days(self, operand: Any, other_date: Any) -> pl.Expr:
        """
        Calculate difference in days between two dates.

        Args:
            operand: First date
            other_date: Second date

        Returns:
            pl.Expr with day difference (operand - other_date)
        """
        # Subtract dates to get duration, then extract days
        return (operand - other_date).dt.total_days()

    def dt_diff_hours(self, operand: Any, other_datetime: Any) -> pl.Expr:
        """
        Calculate difference in hours between two datetimes.

        Args:
            operand: First datetime
            other_datetime: Second datetime

        Returns:
            pl.Expr with hour difference (operand - other_datetime)
        """
        return (operand - other_datetime).dt.total_hours()

    def dt_diff_minutes(self, operand: Any, other_datetime: Any) -> pl.Expr:
        """
        Calculate difference in minutes between two datetimes.

        Args:
            operand: First datetime
            other_datetime: Second datetime

        Returns:
            pl.Expr with minute difference (operand - other_datetime)
        """
        return (operand - other_datetime).dt.total_minutes()

    def dt_diff_seconds(self, operand: Any, other_datetime: Any) -> pl.Expr:
        """
        Calculate difference in seconds between two datetimes.

        Args:
            operand: First datetime
            other_datetime: Second datetime

        Returns:
            pl.Expr with second difference (operand - other_datetime)
        """
        return (operand - other_datetime).dt.total_seconds()

    def dt_diff_milliseconds(self, operand: Any, other_datetime: Any) -> pl.Expr:
        """
        Calculate difference in milliseconds between two datetimes.

        Args:
            operand: First datetime
            other_datetime: Second datetime

        Returns:
            pl.Expr with millisecond difference (operand - other_datetime)

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Using total_milliseconds() method.
        """
        return (operand - other_datetime).dt.total_milliseconds()

    # ========================================
    # Temporal Manipulation Operations
    # ========================================

    def dt_truncate(self, operand: Any, unit: Any) -> pl.Expr:
        """
        Truncate datetime to specified unit using Polars dt.truncate().

        Args:
            operand: Datetime expression
            unit: Unit string ('1d', '1h', '1mo', '1y', etc.)

        Returns:
            pl.Expr truncated to unit
        """
        return operand.dt.truncate(unit)

    def dt_offset_by(self, operand: Any, offset: Any) -> pl.Expr:
        """
        Add/subtract flexible duration using Polars dt.offset_by().

        Args:
            operand: Datetime expression
            offset: Duration string (e.g., "1d", "2h30m", "-3mo")

        Returns:
            pl.Expr with offset applied
        """
        return operand.dt.offset_by(offset)

    # ========================================
    # Temporal Snapshot Operations
    # ========================================

    def dt_today(self) -> pl.Expr:
        """
        Return today's date as a literal expression.

        Returns:
            pl.Expr representing today's date
        """
        from datetime import date
        return pl.lit(date.today())

    def dt_now(self) -> pl.Expr:
        """
        Return current datetime as a literal expression.

        Returns:
            pl.Expr representing current datetime
        """
        from datetime import datetime
        return pl.lit(datetime.now())
