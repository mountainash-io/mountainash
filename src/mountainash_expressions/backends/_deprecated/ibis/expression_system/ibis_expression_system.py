"""Ibis backend implementation of ExpressionSystem."""

from typing import Any, List
import warnings
import ibis
import ibis.expr.types as ir
from ibis.common.deferred import Deferred

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS


class IbisExpressionSystem(ExpressionSystem):
    """
    Ibis-specific implementation of ExpressionSystem.

    This class encapsulates all Ibis-specific operations,
    allowing visitors to build expressions without direct knowledge
    of the Ibis API.

    Note: Ibis uses a special column reference syntax: ibis._[column_name]
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return Ibis backend type."""
        return CONST_VISITOR_BACKENDS.IBIS

    def _warn_if_reverse_operator_bug(self, left: Any, right: Any, operation: str) -> None:
        """
        Warn if encountering known Ibis bug with reverse operators.

        Ibis has a bug where literal + Deferred fails with InputTypeError.
        This affects: literal(n) + ibis._['col'], literal(n) - ibis._['col'], etc.

        Issue: Reverse arithmetic operators fail with Deferred column references
        Affects: Ibis versions <= 11.0.0 (and possibly later)

        This warning alerts users that expressions like `5 + ma.col("x")` may fail
        at runtime with Ibis, even though they work with other backends.

        Args:
            left: Left operand
            right: Right operand
            operation: Operation name (for warning message)

        See: docs/_IBIS_REVERSE_OPERATOR_BUG_FIX.md for details
        """
        # Check if left is a literal scalar and right is a Deferred column reference
        is_left_scalar = isinstance(left, (ir.IntegerScalar, ir.FloatingScalar, ir.BooleanScalar, ir.Scalar))
        is_right_deferred = isinstance(right, Deferred)

        if is_left_scalar and is_right_deferred:
            warnings.warn(
                f"Detected potential Ibis reverse operator bug: {operation} with literal on left "
                f"and column reference on right may fail with InputTypeError. "
                f"This is a known Ibis bug affecting versions <= 11.0.0. "
                f"Consider rewriting as 'ma.col(x) {operation} value' instead of 'value {operation} ma.col(x)'. "
                f"See docs/_IBIS_REVERSE_OPERATOR_BUG_FIX.md for details.",
                UserWarning,
                stacklevel=4
            )

    # ========================================
    # Core Primitives
    # ========================================

    def col(self, name: str, **kwargs) -> ir.Expr:
        """
        Create an Ibis column reference expression.

        Args:
            name: Column name
            **kwargs: Additional options (unused in Ibis)

        Returns:
            ir.Expr representing the column reference

        Note: Ibis uses the special syntax ibis._[column_name]
        """
        return ibis._[name]

    def lit(self, value: Any) -> ir.Expr:
        """
        Create an Ibis literal value expression.

        Args:
            value: The literal value (int, float, str, bool, etc.)

        Returns:
            ir.Expr representing the literal value
        """
        return ibis.literal(value)

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(self, left: Any, right: Any) -> ir.Expr:
        """
        Equality comparison using Ibis operator overloading.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing equality comparison
        """
        return left == right

    def ne(self, left: Any, right: Any) -> ir.Expr:
        """
        Inequality comparison using Ibis operator overloading.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing inequality comparison
        """
        return left != right

    def gt(self, left: Any, right: Any) -> ir.Expr:
        """
        Greater-than comparison using Ibis operator overloading.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing greater-than comparison
        """
        return left > right

    def lt(self, left: Any, right: Any) -> ir.Expr:
        """
        Less-than comparison using Ibis operator overloading.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing less-than comparison
        """
        return left < right

    def ge(self, left: Any, right: Any) -> ir.Expr:
        """
        Greater-than-or-equal comparison using Ibis operator overloading.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing greater-than-or-equal comparison
        """
        return left >= right

    def le(self, left: Any, right: Any) -> ir.Expr:
        """
        Less-than-or-equal comparison using Ibis operator overloading.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing less-than-or-equal comparison
        """
        return left <= right

    # ========================================
    # Arithmetic Operations
    # ========================================

    def add(self, left: Any, right: Any) -> ir.Expr:
        """
        Addition operation using Ibis + operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing addition
        """
        return left + right

    def subtract(self, left: Any, right: Any) -> ir.Expr:
        """
        Subtraction operation using Ibis - operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing subtraction
        """
        self._warn_if_reverse_operator_bug(left, right, '-')
        return left - right

    def multiply(self, left: Any, right: Any) -> ir.Expr:
        """
        Multiplication operation using Ibis * operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing multiplication
        """
        self._warn_if_reverse_operator_bug(left, right, '*')
        return left * right

    def divide(self, left: Any, right: Any) -> ir.Expr:
        """
        Division operation using Ibis / operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing division
        """
        self._warn_if_reverse_operator_bug(left, right, '/')
        return left / right

    def modulo(self, left: Any, right: Any) -> ir.Expr:
        """
        Modulo operation using Ibis % operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing modulo
        """
        self._warn_if_reverse_operator_bug(left, right, '%')
        return left % right

    def power(self, left: Any, right: Any) -> ir.Expr:
        """
        Exponentiation operation using Ibis ** operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing exponentiation
        """
        self._warn_if_reverse_operator_bug(left, right, '**')
        return left ** right

    def floor_divide(self, left: Any, right: Any) -> ir.Expr:
        """
        Floor division operation using Ibis // operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing floor division
        """
        self._warn_if_reverse_operator_bug(left, right, '//')
        return left // right

    # ========================================
    # String Operations
    # ========================================

    def str_upper(self, operand: Any) -> ir.Expr:
        """Convert string to uppercase using Ibis upper()."""
        return operand.upper()

    def str_lower(self, operand: Any) -> ir.Expr:
        """Convert string to lowercase using Ibis lower()."""
        return operand.lower()

    def str_trim(self, operand: Any) -> ir.Expr:
        """Trim whitespace from both sides using Ibis strip()."""
        return operand.strip()

    def str_ltrim(self, operand: Any) -> ir.Expr:
        """Trim whitespace from left side using Ibis lstrip()."""
        return operand.lstrip()

    def str_rtrim(self, operand: Any) -> ir.Expr:
        """Trim whitespace from right side using Ibis rstrip()."""
        return operand.rstrip()

    def str_substring(self, operand: Any, start: int, length: int = None) -> ir.Expr:
        """Extract substring using Ibis substr()."""
        if length is None:
            # From start to end - use substr with large length
            return operand.substr(start)
        else:
            # From start with specific length
            return operand.substr(start, length)

    def str_concat(self, operand: Any, *others: Any, separator: str = "") -> ir.Expr:
        """Concatenate strings using Ibis concat()."""
        if separator:
            # Join with separator
            parts = [operand]
            for other in others:
                parts.append(ibis.literal(separator))
                parts.append(other)
            return ibis.literal("").join(parts)
        else:
            # Simple concatenation
            result = operand
            for other in others:
                result = result + other
            return result

    def str_length(self, operand: Any) -> ir.Expr:
        """Get string length using Ibis length()."""
        return operand.length()

    def str_replace(self, operand: Any, old: str, new: str) -> ir.Expr:
        """Replace substring using Ibis replace()."""
        return operand.replace(old, new)

    def str_contains(self, operand: Any, substring: str) -> ir.Expr:
        """Check if string contains substring using Ibis contains()."""
        return operand.contains(substring)

    def str_starts_with(self, operand: Any, prefix: str) -> ir.Expr:
        """Check if string starts with prefix using Ibis startswith()."""
        return operand.startswith(prefix)

    def str_ends_with(self, operand: Any, suffix: str) -> ir.Expr:
        """Check if string ends with suffix using Ibis endswith()."""
        return operand.endswith(suffix)

    # ========================================
    # Logical Operations
    # ========================================

    def and_(self, left: Any, right: Any) -> ir.Expr:
        """
        Logical AND operation using Ibis & operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing logical AND
        """
        return left & right

    def or_(self, left: Any, right: Any) -> ir.Expr:
        """
        Logical OR operation using Ibis | operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing logical OR
        """
        return left | right

    def not_(self, operand: Any) -> ir.Expr:
        """
        Logical NOT operation using Ibis ~ operator.

        Args:
            operand: Operand to negate (ir.Expr)

        Returns:
            ir.Expr representing logical NOT
        """
        return ~operand

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(self, element: Any, collection: List[Any]) -> ir.Expr:
        """
        Membership test using Ibis isin() method.

        Args:
            element: Element expression to check (ir.Expr)
            collection: List of values to check against

        Returns:
            ir.Expr representing membership test
        """
        return element.isin(collection)

    # ========================================
    # Null Operations
    # ========================================

    def is_null(self, operand: Any) -> ir.Expr:
        """
        Check if operand is NULL using Ibis isnull() method.

        Args:
            operand: Operand to check (ir.Expr)

        Returns:
            ir.Expr representing null check
        """
        return operand.isnull()

    # ========================================
    # Type Operations
    # ========================================

    def cast(self, value: Any, dtype: Any, **kwargs) -> ir.Expr:
        """
        Cast value to specified type using Ibis cast() method.

        Args:
            value: Value expression to cast (ir.Expr)
            dtype: Target data type (can be string like 'int32' or Ibis type)
            **kwargs: Additional casting options (unused in Ibis)

        Returns:
            ir.Expr representing casted value
        """
        return value.cast(dtype)

    # ========================================
    # Arithmetic Operations (Legacy aliases)
    # ========================================

    def add(self, left: Any, right: Any) -> ir.Expr:
        """
        Addition operation using Ibis + operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing addition
        """
        self._warn_if_reverse_operator_bug(left, right, '+')
        return left + right

    def sub(self, left: Any, right: Any) -> ir.Expr:
        """
        Subtraction operation using Ibis - operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing subtraction
        """
        self._warn_if_reverse_operator_bug(left, right, '-')
        return left - right

    def mul(self, left: Any, right: Any) -> ir.Expr:
        """
        Multiplication operation using Ibis * operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing multiplication
        """
        self._warn_if_reverse_operator_bug(left, right, '*')
        return left * right

    def mod(self, left: Any, right: Any) -> ir.Expr:
        """
        Modulo operation using Ibis % operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing modulo
        """
        self._warn_if_reverse_operator_bug(left, right, '%')
        return left % right

    # ========================================
    # Pattern Matching Operations
    # ========================================

    def pattern_like(self, operand: Any, pattern: str) -> ir.Expr:
        """
        SQL LIKE pattern matching using Ibis like() method.

        Note: The Ibis Polars backend does not support LIKE operations.
        This is an upstream limitation in Ibis.
        """
        return operand.like(pattern)

    def pattern_regex_match(self, operand: Any, pattern: str) -> ir.Expr:
        """
        Check if string fully matches regex pattern.
        Ibis re_search returns a boolean directly.
        """
        # For full match, anchor the pattern
        if not pattern.startswith('^'):
            pattern = '^' + pattern
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        return operand.re_search(pattern)

    def pattern_regex_contains(self, operand: Any, pattern: str) -> ir.Expr:
        """
        Check if string contains regex pattern.
        Ibis re_search returns a boolean directly.
        """
        return operand.re_search(pattern)

    def pattern_regex_replace(self, operand: Any, pattern: str, replacement: str) -> ir.Expr:
        """
        Replace text matching regex pattern using Ibis re_replace().
        """
        return operand.re_replace(pattern, replacement)

    # ========================================
    # Conditional Operations
    # ========================================

    def conditional_when(self, condition: Any, consequence: Any, alternative: Any) -> ir.Expr:
        """
        Conditional if-then-else using Ibis ifelse().
        """
        return condition.ifelse(consequence, alternative)

    def conditional_coalesce(self, values: List[Any]) -> ir.Expr:
        """
        Return first non-null value using Ibis coalesce().
        """
        return ibis.coalesce(*values)

    def conditional_fill_null(self, operand: Any, fill_value: Any) -> ir.Expr:
        """
        Replace null values using Ibis fill_null().
        """
        # Use fill_null instead of fillna (deprecated in v9.1+)
        if hasattr(operand, 'fill_null'):
            return operand.fill_null(fill_value)
        else:
            # Fallback for older versions
            return operand.fillna(fill_value)

    # ========================================
    # Temporal Operations
    # ========================================

    def temporal_year(self, operand: Any) -> ir.Expr:
        """Extract year from datetime using Ibis year()."""
        return operand.year()

    def temporal_month(self, operand: Any) -> ir.Expr:
        """Extract month from datetime using Ibis month()."""
        return operand.month()

    def temporal_day(self, operand: Any) -> ir.Expr:
        """Extract day from datetime using Ibis day()."""
        return operand.day()

    def temporal_hour(self, operand: Any) -> ir.Expr:
        """Extract hour from datetime using Ibis hour()."""
        return operand.hour()

    def temporal_minute(self, operand: Any) -> ir.Expr:
        """Extract minute from datetime using Ibis minute()."""
        return operand.minute()

    def temporal_second(self, operand: Any) -> ir.Expr:
        """Extract second from datetime using Ibis second()."""
        return operand.second()

    def temporal_weekday(self, operand: Any) -> ir.Expr:
        """
        Extract day of week from datetime using Ibis day_of_week.
        Note: Ibis returns ISO weekday (1=Monday, 7=Sunday),
        we convert to 0=Monday, 6=Sunday for consistency.
        """
        # Get ISO weekday (1-7) and subtract 1 to get (0-6)
        return operand.day_of_week.index() - 1

    def temporal_week(self, operand: Any) -> ir.Expr:
        """Extract week number from datetime using Ibis week_of_year()."""
        return operand.week_of_year()

    def temporal_quarter(self, operand: Any) -> ir.Expr:
        """Extract quarter from datetime using Ibis quarter()."""
        return operand.quarter()

    def temporal_add_days(self, operand: Any, days: Any) -> ir.Expr:
        """Add days to a date - supports both literals and expressions."""
        return self._temporal_duration_add(operand, days, 'days', 'D')

    def temporal_add_months(self, operand: Any, months: Any) -> ir.Expr:
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
                    "Only literal values are supported for temporal_add_months()."
                )
        else:
            return operand + ibis.interval(months=months)

    def temporal_add_years(self, operand: Any, years: Any) -> ir.Expr:
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
                    "Only literal values are supported for temporal_add_years()."
                )
        else:
            return operand + ibis.interval(years=years)

    def temporal_diff_days(self, operand: Any, other_date: Any) -> ir.Expr:
        """
        Calculate difference in days between two dates.

        Args:
            operand: First date
            other_date: Second date

        Returns:
            Difference in days (operand - other_date)
        """
        # Subtract dates to get interval, then extract days
        # In Ibis, date subtraction returns an interval
        diff = operand.delta(other_date, 'day')
        return diff

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
                # Literal expression → extract value and use ibis.interval()
                scalar_value = value.op().value
                return operand + ibis.interval(**{unit: scalar_value})
            else:
                # Column, Deferred, or complex expression → cast to Interval for vectorized operation
                value_interval = value.cast(dt.Interval(interval_unit))
                return operand + value_interval
        else:
            # Raw Python value → use ibis.interval() for readability
            return operand + ibis.interval(**{unit: value})

    def temporal_add_hours(self, operand: Any, hours: Any) -> ir.Expr:
        """Add hours to a datetime - supports both literals and expressions."""
        return self._temporal_duration_add(operand, hours, 'hours', 'h')

    def temporal_add_minutes(self, operand: Any, minutes: Any) -> ir.Expr:
        """Add minutes to a datetime - supports both literals and expressions."""
        return self._temporal_duration_add(operand, minutes, 'minutes', 'm')

    def temporal_add_seconds(self, operand: Any, seconds: Any) -> ir.Expr:
        """Add seconds to a datetime - supports both literals and expressions."""
        return self._temporal_duration_add(operand, seconds, 'seconds', 's')

    def temporal_diff_hours(self, operand: Any, other_datetime: Any) -> ir.Expr:
        """
        Calculate difference in hours between two datetimes.

        Note: Uses epoch_seconds() approach for universal backend compatibility.
        The .delta() method is not supported by all Ibis backends (e.g., Polars).
        """
        return (operand.epoch_seconds() - other_datetime.epoch_seconds()) // 3600

    def temporal_diff_minutes(self, operand: Any, other_datetime: Any) -> ir.Expr:
        """
        Calculate difference in minutes between two datetimes.

        Note: Uses epoch_seconds() approach for universal backend compatibility.
        The .delta() method is not supported by all Ibis backends (e.g., Polars).
        """
        return (operand.epoch_seconds() - other_datetime.epoch_seconds()) // 60

    def temporal_diff_seconds(self, operand: Any, other_datetime: Any) -> ir.Expr:
        """
        Calculate difference in seconds between two datetimes.

        Note: Uses epoch_seconds() approach for universal backend compatibility.
        The .delta() method is not supported by all Ibis backends (e.g., Polars).
        """
        return operand.epoch_seconds() - other_datetime.epoch_seconds()

    def temporal_diff_months(self, operand: Any, other_date: Any) -> ir.Expr:
        """
        Calculate difference in months between two dates.
        Note: Approximate calculation using year and month components.
        """
        years_diff = operand.year() - other_date.year()
        months_diff = operand.month() - other_date.month()
        return years_diff * 12 + months_diff

    def temporal_diff_years(self, operand: Any, other_date: Any) -> ir.Expr:
        """Calculate difference in years between two dates."""
        return operand.year() - other_date.year()

    def temporal_truncate(self, operand: Any, unit: Any) -> ir.Expr:
        """
        Truncate datetime to specified unit using Ibis truncate().

        Args:
            operand: Datetime expression
            unit: Unit string (Polars-style like "1d", "1h" or Ibis-style like "D", "day")

        Note: Converts Polars-style duration strings (e.g., "1d") to Ibis IntervalUnit
        values (e.g., "D" or "day").
        """
        # Convert Polars-style duration string to Ibis IntervalUnit
        ibis_unit = self._convert_to_ibis_truncate_unit(unit)
        return operand.truncate(ibis_unit)

    def _convert_to_ibis_truncate_unit(self, unit: str) -> str:
        """
        Convert Polars-style duration string to Ibis IntervalUnit.

        Args:
            unit: Duration string like "1d", "1h", "1mo", "1y" (Polars style)
                  or "D", "day", "h", "hour" (Ibis style)

        Returns:
            Ibis IntervalUnit string

        Examples:
            "1d" -> "D"
            "1h" -> "h"
            "1mo" -> "M"
            "D" -> "D" (passthrough)
        """
        import re

        # If it's already an Ibis-style unit (single letter or word), pass through
        if not re.match(r'^\d+', unit):
            return unit

        # Parse Polars-style: number + unit
        match = re.match(r'^\d+(y|mo|d|h|m|s|w)$', unit)
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

    def temporal_offset_by(self, operand: Any, offset: Any) -> ir.Expr:
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

    def _parse_duration_string(self, duration: str) -> list:
        """
        Parse a duration string into Ibis intervals.

        Args:
            duration: Duration string like "1d2h", "-3mo", "2h30m"

        Returns:
            List of ibis.interval() objects

        Examples:
            "1d2h" -> [interval(days=1), interval(hours=2)]
            "-3mo" -> [interval(months=-3)]
            "2h30m" -> [interval(hours=2), interval(minutes=30)]
        """
        import re

        # Handle negative sign
        is_negative = duration.startswith('-')
        if is_negative:
            duration = duration[1:]

        intervals = []

        # Pattern: number followed by unit
        # Units: y, mo, d, h, m, s
        # Need to handle 'mo' before 'm' to avoid confusion
        pattern = r'(\d+)(y|mo|d|h|m|s)'

        matches = re.findall(pattern, duration)

        for value_str, unit in matches:
            value = int(value_str)
            if is_negative:
                value = -value

            # Map unit to ibis.interval parameter
            if unit == 'y':
                intervals.append(ibis.interval(years=value))
            elif unit == 'mo':
                intervals.append(ibis.interval(months=value))
            elif unit == 'd':
                intervals.append(ibis.interval(days=value))
            elif unit == 'h':
                intervals.append(ibis.interval(hours=value))
            elif unit == 'm':
                intervals.append(ibis.interval(minutes=value))
            elif unit == 's':
                intervals.append(ibis.interval(seconds=value))

        return intervals
