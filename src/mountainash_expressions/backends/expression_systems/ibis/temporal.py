"""Ibis temporal operations implementation."""

from typing import Any
import re
import ibis
import ibis.expr.types as ir

from .base import IbisBaseExpressionSystem
from ....core.protocols import TemporalExpressionProtocol


class IbisTemporalExpressionSystem(IbisBaseExpressionSystem, TemporalExpressionProtocol):
    """
    Ibis implementation of temporal/datetime operations.

    Note:
        Uses epoch_seconds() approach for diff operations for universal backend compatibility.
        The .delta() method is not supported by all Ibis backends (e.g., Polars).
    """

    # ========================================
    # Helper Methods
    # ========================================

    def _temporal_duration_add(self, operand: Any, value: Any, unit: str, interval_unit: str) -> ir.Expr:
        """
        Helper for adding duration-based temporal units (days, hours, minutes, seconds).

        Args:
            operand: Timestamp/date expression to add to
            value: Duration value (literal, Expr, or Deferred)
            unit: Unit name for ibis.interval() (e.g., 'hours', 'days')
            interval_unit: Unit code for Interval datatype (e.g., 'h', 'D')

        Returns:
            Expression with duration added
        """
        import ibis.expr.datatypes as dt
        from ibis.common.deferred import Deferred

        # Check if it's a backend expression (Expr or Deferred)
        if isinstance(value, (ir.Expr, Deferred)):
            # For Expr, check if it's a literal
            if isinstance(value, ir.Expr) and hasattr(value, 'op') and hasattr(value.op(), 'value'):
                # Literal expression -> extract value and use ibis.interval()
                scalar_value = value.op().value
                return operand + ibis.interval(**{unit: scalar_value})
            else:
                # Column, Deferred, or complex expression -> cast to Interval for vectorized operation
                value_interval = value.cast(dt.Interval(interval_unit))
                return operand + value_interval
        else:
            # Raw Python value -> use ibis.interval() for readability
            return operand + ibis.interval(**{unit: value})

    def _convert_to_ibis_truncate_unit(self, unit: str) -> str:
        """
        Convert Polars-style duration string to Ibis IntervalUnit.

        Args:
            unit: Duration string like "1d", "1h", "1mo", "1y" (Polars style)
                  or "D", "day", "h", "hour" (Ibis style)

        Returns:
            Ibis IntervalUnit string
        """
        # If it's already an Ibis-style unit (single letter or word), pass through
        if not re.match(r'^\d+', str(unit)):
            return unit

        # Parse Polars-style: number + unit
        match = re.match(r'^\d+(y|mo|d|h|m|s|w)$', str(unit))
        if not match:
            # If it doesn't match expected pattern, pass through and let Ibis handle it
            return unit

        unit_code = match.group(1)

        # Map to Ibis IntervalUnit codes
        unit_mapping = {
            'y': 'Y',    # year
            'mo': 'M',   # month
            'w': 'W',    # week
            'd': 'D',    # day
            'h': 'h',    # hour
            'm': 'm',    # minute
            's': 's',    # second
        }

        return unit_mapping.get(unit_code, unit)

    def _parse_duration_string(self, duration: str) -> list:
        """
        Parse a duration string into Ibis intervals.

        Args:
            duration: Duration string like "1d2h", "-3mo", "2h30m"

        Returns:
            List of ibis.interval() objects
        """
        # Handle negative sign
        is_negative = duration.startswith('-')
        if is_negative:
            duration = duration[1:]

        intervals = []

        # Pattern: number followed by unit
        # Units: y, mo, w, d, h, m, s (need to handle 'mo' before 'm')
        pattern = r'(\d+)(y|mo|w|d|h|m|s)'

        # Map short codes to ibis.interval() kwargs
        unit_mapping = {
            'y': 'years',
            'mo': 'months',
            'w': 'weeks',
            'd': 'days',
            'h': 'hours',
            'm': 'minutes',
            's': 'seconds',
        }

        for match in re.finditer(pattern, duration):
            amount = int(match.group(1))
            unit_code = match.group(2)

            if is_negative:
                amount = -amount

            unit_name = unit_mapping.get(unit_code)
            if unit_name:
                intervals.append(ibis.interval(**{unit_name: amount}))

        return intervals

    # ========================================
    # Extraction Operations
    # ========================================

    def dt_year(self, operand: Any) -> ir.Expr:
        """Extract year from datetime using Ibis year()."""
        return operand.year()

    def dt_month(self, operand: Any) -> ir.Expr:
        """Extract month from datetime using Ibis month()."""
        return operand.month()

    def dt_day(self, operand: Any) -> ir.Expr:
        """Extract day from datetime using Ibis day()."""
        return operand.day()

    def dt_hour(self, operand: Any) -> ir.Expr:
        """Extract hour from datetime using Ibis hour()."""
        return operand.hour()

    def dt_minute(self, operand: Any) -> ir.Expr:
        """Extract minute from datetime using Ibis minute()."""
        return operand.minute()

    def dt_second(self, operand: Any) -> ir.Expr:
        """Extract second from datetime using Ibis second()."""
        return operand.second()

    def dt_weekday(self, operand: Any) -> ir.Expr:
        """
        Extract day of week from datetime.
        Note: Ibis returns ISO weekday (1=Monday, 7=Sunday),
        we convert to 0=Monday, 6=Sunday for consistency.
        """
        return operand.day_of_week.index()

    def dt_week(self, operand: Any) -> ir.Expr:
        """Extract week number from datetime using Ibis week_of_year()."""
        return operand.week_of_year()

    def dt_quarter(self, operand: Any) -> ir.Expr:
        """Extract quarter from datetime using Ibis quarter()."""
        return operand.quarter()

    # ========================================
    # Addition Operations
    # ========================================

    def dt_add_days(self, operand: Any, days: Any) -> ir.Expr:
        """Add days to a date - supports both literals and expressions."""
        return self._temporal_duration_add(operand, days, 'days', 'D')

    def dt_add_months(self, operand: Any, months: Any) -> ir.Expr:
        """
        Add months to a date - literal values only.

        Note: Months are calendar-based (variable length), not duration-based.
        Ibis does not support vectorized month arithmetic via Interval casting.
        """
        if isinstance(months, ir.Expr):
            # Try to extract literal value if it's an Ibis literal expression
            if hasattr(months, 'op') and hasattr(months.op(), 'value'):
                months_value = months.op().value
                return operand + ibis.interval(months=months_value)
            else:
                raise NotImplementedError(
                    "Ibis does not support vectorized month arithmetic with column expressions. "
                    "Only literal values are supported for dt_add_months()."
                )
        else:
            return operand + ibis.interval(months=months)

    def dt_add_years(self, operand: Any, years: Any) -> ir.Expr:
        """
        Add years to a date - literal values only.

        Note: Years are calendar-based (variable length), not duration-based.
        Ibis does not support vectorized year arithmetic via Interval casting.
        """
        if isinstance(years, ir.Expr):
            # Try to extract literal value if it's an Ibis literal expression
            if hasattr(years, 'op') and hasattr(years.op(), 'value'):
                years_value = years.op().value
                return operand + ibis.interval(years=years_value)
            else:
                raise NotImplementedError(
                    "Ibis does not support vectorized year arithmetic with column expressions. "
                    "Only literal values are supported for dt_add_years()."
                )
        else:
            return operand + ibis.interval(years=years)

    def dt_add_hours(self, operand: Any, hours: Any) -> ir.Expr:
        """Add hours to a datetime - supports both literals and expressions."""
        return self._temporal_duration_add(operand, hours, 'hours', 'h')

    def dt_add_minutes(self, operand: Any, minutes: Any) -> ir.Expr:
        """Add minutes to a datetime - supports both literals and expressions."""
        return self._temporal_duration_add(operand, minutes, 'minutes', 'm')

    def dt_add_seconds(self, operand: Any, seconds: Any) -> ir.Expr:
        """Add seconds to a datetime - supports both literals and expressions."""
        return self._temporal_duration_add(operand, seconds, 'seconds', 's')

    # ========================================
    # Difference Operations
    # ========================================

    def dt_diff_years(self, operand: Any, other_date: Any) -> ir.Expr:
        """Calculate difference in years between two dates."""
        return operand.year() - other_date.year()

    def dt_diff_months(self, operand: Any, other_date: Any) -> ir.Expr:
        """
        Calculate difference in months between two dates.
        Note: Approximate calculation using year and month components.
        """
        years_diff = operand.year() - other_date.year()
        months_diff = operand.month() - other_date.month()
        return years_diff * 12 + months_diff

    def dt_diff_days(self, operand: Any, other_date: Any) -> ir.Expr:
        """Calculate difference in days between two dates."""
        return operand.delta(other_date, 'day')

    def dt_diff_hours(self, operand: Any, other_datetime: Any) -> ir.Expr:
        """
        Calculate difference in hours between two datetimes.

        Note: Uses epoch_seconds() approach for universal backend compatibility.
        The .delta() method is not supported by all Ibis backends (e.g., Polars).
        """
        return (operand.epoch_seconds() - other_datetime.epoch_seconds()) // 3600

    def dt_diff_minutes(self, operand: Any, other_datetime: Any) -> ir.Expr:
        """
        Calculate difference in minutes between two datetimes.

        Note: Uses epoch_seconds() approach for universal backend compatibility.
        """
        return (operand.epoch_seconds() - other_datetime.epoch_seconds()) // 60

    def dt_diff_seconds(self, operand: Any, other_datetime: Any) -> ir.Expr:
        """
        Calculate difference in seconds between two datetimes.

        Note: Uses epoch_seconds() approach for universal backend compatibility.
        """
        return operand.epoch_seconds() - other_datetime.epoch_seconds()

    def dt_diff_milliseconds(self, operand: Any, other_datetime: Any) -> ir.Expr:
        """Calculate difference in milliseconds between two datetimes."""
        return (operand.epoch_seconds() - other_datetime.epoch_seconds()) * 1000

    # ========================================
    # Manipulation Operations
    # ========================================

    def dt_truncate(self, operand: Any, unit: Any) -> ir.Expr:
        """
        Truncate datetime to specified unit using Ibis truncate().

        Args:
            operand: Datetime expression
            unit: Unit string (Polars-style like "1d", "1h" or Ibis-style like "D", "day")

        Note: Converts Polars-style duration strings (e.g., "1d") to Ibis IntervalUnit
        values (e.g., "D" or "day").
        """
        ibis_unit = self._convert_to_ibis_truncate_unit(unit)
        return operand.truncate(ibis_unit)

    def dt_offset_by(self, operand: Any, offset: Any) -> ir.Expr:
        """
        Add/subtract flexible duration.

        Args:
            operand: Datetime expression
            offset: Duration string (e.g., "1d", "2h", "-3mo", "1d2h")

        Note: This parses the offset string and constructs ibis.interval().
        Supports: y (years), mo (months), d (days), h (hours), m (minutes), s (seconds)
        """
        # Parse the duration string and build intervals
        intervals = self._parse_duration_string(offset)

        # Apply all intervals to the operand
        result = operand
        for interval in intervals:
            result = result + interval

        return result

    # ========================================
    # Snapshot Operations
    # ========================================

    def dt_today(self) -> ir.Expr:
        """
        Return today's date as a literal expression.

        Returns:
            ir.Expr representing today's date
        """
        from datetime import date
        return ibis.literal(date.today())

    def dt_now(self) -> ir.Expr:
        """
        Return current datetime as a literal expression.

        Returns:
            ir.Expr representing current datetime
        """
        from datetime import datetime
        return ibis.literal(datetime.now())
