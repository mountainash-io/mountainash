"""Narwhals temporal operations implementation."""

from typing import Any
import re
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import TemporalExpressionProtocol


class NarwhalsTemporalExpressionSystem(NarwhalsBaseExpressionSystem, TemporalExpressionProtocol):
    """
    Narwhals implementation of temporal/datetime operations.

    Note:
        Narwhals offset_by() only accepts string literals, not expressions.
        Use _extract_literal_value() to handle this limitation.
    """

    # ========================================
    # Helper Methods
    # ========================================

    def _extract_literal_value(self, value: Any) -> Any:
        """
        Extract the literal value from a Narwhals Expr if it's a literal.

        Args:
            value: Either a raw Python value or a nw.Expr

        Returns:
            The raw Python value

        Raises:
            ValueError: If the Expr is not a literal (e.g., column reference)
        """
        if not isinstance(value, nw.Expr):
            # Already a raw value
            return value

        # Try to extract literal value from Expr string representation
        str_repr = str(value)
        if str_repr.startswith('lit(value='):
            # Extract value from: "lit(value=2, dtype=None)"
            match = re.search(r'lit\(value=([^,]+)', str_repr)
            if match:
                return eval(match.group(1))

        # Not a literal - must be column reference or other expression
        raise ValueError(
            "Narwhals backend does not support column expressions for temporal operations. "
            "Use literal values only."
        )

    def _parse_duration_string(self, duration: str) -> list:
        """
        Parse a duration string into Narwhals-compatible offset strings.

        Args:
            duration: Duration string like "1d2h", "-3mo", "2h30m"

        Returns:
            List of offset strings for Narwhals (e.g., ["1d", "2h"])
        """
        # Handle negative sign
        is_negative = duration.startswith('-')
        if is_negative:
            duration = duration[1:]

        components = []

        # Pattern: number followed by unit
        # Units: y, mo, w, d, h, m, s (need to handle 'mo' before 'm')
        pattern = r'(\d+)(y|mo|w|d|h|m|s)'

        for match in re.finditer(pattern, duration):
            amount = int(match.group(1))
            unit = match.group(2)

            if is_negative:
                amount = -amount

            components.append(f"{amount}{unit}")

        return components

    # ========================================
    # Extraction Operations
    # ========================================

    def dt_year(self, operand: Any) -> nw.Expr:
        return operand.dt.year()

    def dt_month(self, operand: Any) -> nw.Expr:
        return operand.dt.month()

    def dt_day(self, operand: Any) -> nw.Expr:
        return operand.dt.day()

    def dt_hour(self, operand: Any) -> nw.Expr:
        return operand.dt.hour()

    def dt_minute(self, operand: Any) -> nw.Expr:
        return operand.dt.minute()

    def dt_second(self, operand: Any) -> nw.Expr:
        return operand.dt.second()

    def dt_weekday(self, operand: Any) -> nw.Expr:
        """Extract weekday (0=Monday, 6=Sunday)."""
        return operand.dt.weekday()

    def dt_week(self, operand: Any) -> nw.Expr:
        return operand.dt.week()

    def dt_quarter(self, operand: Any) -> nw.Expr:
        """Extract quarter from datetime."""
        # Check if dt.quarter() is available
        if hasattr(operand.dt, 'quarter'):
            return operand.dt.quarter()
        else:
            # Calculate quarter from month: Q1(1-3), Q2(4-6), Q3(7-9), Q4(10-12)
            month = operand.dt.month()
            return ((month - 1) // 3 + 1)

    # ========================================
    # Addition Operations
    # ========================================

    def dt_add_days(self, operand: Any, days: Any) -> nw.Expr:
        """Add days to a date using Narwhals dt.offset_by()."""
        days = self._extract_literal_value(days)
        return operand.dt.offset_by(f"{days}d")

    def dt_add_months(self, operand: Any, months: Any) -> nw.Expr:
        """Add months to a date using Narwhals dt.offset_by()."""
        months = self._extract_literal_value(months)
        return operand.dt.offset_by(f"{months}mo")

    def dt_add_years(self, operand: Any, years: Any) -> nw.Expr:
        """Add years to a date using Narwhals dt.offset_by()."""
        years = self._extract_literal_value(years)
        return operand.dt.offset_by(f"{years}y")

    def dt_add_hours(self, operand: Any, hours: Any) -> nw.Expr:
        """Add hours to a datetime using Narwhals dt.offset_by()."""
        hours = self._extract_literal_value(hours)
        return operand.dt.offset_by(f"{hours}h")

    def dt_add_minutes(self, operand: Any, minutes: Any) -> nw.Expr:
        """Add minutes to a datetime using Narwhals dt.offset_by()."""
        minutes = self._extract_literal_value(minutes)
        return operand.dt.offset_by(f"{minutes}m")

    def dt_add_seconds(self, operand: Any, seconds: Any) -> nw.Expr:
        """Add seconds to a datetime using Narwhals dt.offset_by()."""
        seconds = self._extract_literal_value(seconds)
        return operand.dt.offset_by(f"{seconds}s")

    # ========================================
    # Difference Operations
    # ========================================

    def dt_diff_years(self, operand: Any, other_date: Any) -> nw.Expr:
        """Calculate difference in years between two dates."""
        return operand.dt.year() - other_date.dt.year()

    def dt_diff_months(self, operand: Any, other_date: Any) -> nw.Expr:
        """Calculate difference in months between two dates (approximate)."""
        years_diff = operand.dt.year() - other_date.dt.year()
        months_diff = operand.dt.month() - other_date.dt.month()
        return years_diff * 12 + months_diff

    def dt_diff_days(self, operand: Any, other_date: Any) -> nw.Expr:
        """Calculate difference in days between two dates."""
        return (operand - other_date).dt.total_days()

    def dt_diff_hours(self, operand: Any, other_datetime: Any) -> nw.Expr:
        """Calculate difference in hours between two datetimes."""
        # Narwhals may not have total_hours(), use total_seconds() / 3600
        # Floor to match expected integer behavior
        return ((operand - other_datetime).dt.total_seconds() / 3600).floor()

    def dt_diff_minutes(self, operand: Any, other_datetime: Any) -> nw.Expr:
        """Calculate difference in minutes between two datetimes."""
        # Use total_seconds() / 60 for consistency
        return ((operand - other_datetime).dt.total_seconds() / 60).floor()

    def dt_diff_seconds(self, operand: Any, other_datetime: Any) -> nw.Expr:
        """Calculate difference in seconds between two datetimes."""
        return (operand - other_datetime).dt.total_seconds()

    def dt_diff_milliseconds(self, operand: Any, other_datetime: Any) -> nw.Expr:
        """Calculate difference in milliseconds between two datetimes."""
        return (operand - other_datetime).dt.total_milliseconds()

    # ========================================
    # Manipulation Operations
    # ========================================

    def dt_truncate(self, operand: Any, unit: Any) -> nw.Expr:
        """
        Truncate datetime to specified unit using Narwhals dt.truncate().

        Args:
            operand: Datetime expression
            unit: Unit string ('1d', '1h', '1mo', '1y', etc.)
        """
        return operand.dt.truncate(unit)

    def dt_offset_by(self, operand: Any, offset: Any) -> nw.Expr:
        """
        Add/subtract flexible duration using Narwhals dt.offset_by().

        Args:
            operand: Datetime expression
            offset: Duration string (e.g., "1d", "2h30m", "-3mo", "1d2h")

        Note: Narwhals dt.offset_by() only supports single-unit strings,
        so we parse complex strings and apply them sequentially.
        """
        # Parse the duration string into individual components
        components = self._parse_duration_string(offset)

        # Apply each component sequentially
        result = operand
        for component in components:
            result = result.dt.offset_by(component)

        return result

    # ========================================
    # Snapshot Operations
    # ========================================

    def dt_today(self) -> nw.Expr:
        """
        Return today's date as a literal expression.

        Returns:
            nw.Expr representing today's date
        """
        from datetime import date
        return nw.lit(date.today())

    def dt_now(self) -> nw.Expr:
        """
        Return current datetime as a literal expression.

        Returns:
            nw.Expr representing current datetime
        """
        from datetime import datetime
        return nw.lit(datetime.now())
