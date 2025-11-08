"""Polars backend implementation of ExpressionSystem."""

from typing import Any, List
import polars as pl

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS


class PolarsExpressionSystem(ExpressionSystem):
    """
    Polars-specific implementation of ExpressionSystem.

    This class encapsulates all Polars-specific operations,
    allowing visitors to build expressions without direct knowledge
    of the Polars API.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return Polars backend type."""
        return CONST_VISITOR_BACKENDS.POLARS

    # ========================================
    # Core Primitives
    # ========================================

    def col(self, name: str, **kwargs) -> pl.Expr:
        """
        Create a Polars column reference expression.

        Args:
            name: Column name
            **kwargs: Additional options for pl.col()

        Returns:
            pl.Expr representing the column reference
        """
        return pl.col(name, **kwargs)

    def lit(self, value: Any) -> pl.Expr:
        """
        Create a Polars literal value expression.

        Args:
            value: The literal value (int, float, str, bool, etc.)

        Returns:
            pl.Expr representing the literal value
        """
        return pl.lit(value)

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(self, left: Any, right: Any) -> pl.Expr:
        """
        Equality comparison using Polars operator overloading.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing equality comparison
        """
        return left == right

    def ne(self, left: Any, right: Any) -> pl.Expr:
        """
        Inequality comparison using Polars operator overloading.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing inequality comparison
        """
        return left != right

    def gt(self, left: Any, right: Any) -> pl.Expr:
        """
        Greater-than comparison using Polars operator overloading.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing greater-than comparison
        """
        return left > right

    def lt(self, left: Any, right: Any) -> pl.Expr:
        """
        Less-than comparison using Polars operator overloading.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing less-than comparison
        """
        return left < right

    def ge(self, left: Any, right: Any) -> pl.Expr:
        """
        Greater-than-or-equal comparison using Polars operator overloading.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing greater-than-or-equal comparison
        """
        return left >= right

    def le(self, left: Any, right: Any) -> pl.Expr:
        """
        Less-than-or-equal comparison using Polars operator overloading.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing less-than-or-equal comparison
        """
        return left <= right

    # ========================================
    # Arithmetic Operations
    # ========================================

    def add(self, left: Any, right: Any) -> pl.Expr:
        """
        Addition operation using Polars + operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing addition
        """
        return left + right

    def subtract(self, left: Any, right: Any) -> pl.Expr:
        """
        Subtraction operation using Polars - operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing subtraction
        """
        return left - right

    def multiply(self, left: Any, right: Any) -> pl.Expr:
        """
        Multiplication operation using Polars * operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing multiplication
        """
        return left * right

    def divide(self, left: Any, right: Any) -> pl.Expr:
        """
        Division operation using Polars / operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing division
        """
        return left / right

    def modulo(self, left: Any, right: Any) -> pl.Expr:
        """
        Modulo operation using Polars % operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing modulo
        """
        return left % right

    def power(self, left: Any, right: Any) -> pl.Expr:
        """
        Exponentiation operation using Polars ** operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing exponentiation
        """
        return left ** right

    def floor_divide(self, left: Any, right: Any) -> pl.Expr:
        """
        Floor division operation using Polars // operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing floor division
        """
        return left // right

    # ========================================
    # String Operations
    # ========================================

    def str_upper(self, operand: Any) -> pl.Expr:
        """Convert string to uppercase using Polars str.to_uppercase()."""
        return operand.str.to_uppercase()

    def str_lower(self, operand: Any) -> pl.Expr:
        """Convert string to lowercase using Polars str.to_lowercase()."""
        return operand.str.to_lowercase()

    def str_trim(self, operand: Any) -> pl.Expr:
        """Trim whitespace from both sides using Polars str.strip_chars()."""
        return operand.str.strip_chars()

    def str_ltrim(self, operand: Any) -> pl.Expr:
        """Trim whitespace from left side using Polars str.strip_chars_start()."""
        return operand.str.strip_chars_start()

    def str_rtrim(self, operand: Any) -> pl.Expr:
        """Trim whitespace from right side using Polars str.strip_chars_end()."""
        return operand.str.strip_chars_end()

    def str_substring(self, operand: Any, start: int, length: int = None) -> pl.Expr:
        """Extract substring using Polars str.slice()."""
        if length is None:
            # From start to end
            return operand.str.slice(start)
        else:
            # From start with specific length
            return operand.str.slice(start, length)

    def str_concat(self, operand: Any, *others: Any, separator: str = "") -> pl.Expr:
        """Concatenate strings using Polars + operator."""
        result = operand
        for other in others:
            if separator:
                result = result + pl.lit(separator) + other
            else:
                result = result + other
        return result

    def str_length(self, operand: Any) -> pl.Expr:
        """Get string length using Polars str.len_chars()."""
        return operand.str.len_chars()

    def str_replace(self, operand: Any, old: str, new: str) -> pl.Expr:
        """Replace substring using Polars str.replace()."""
        return operand.str.replace(old, new, literal=True)

    def str_contains(self, operand: Any, substring: str) -> pl.Expr:
        """Check if string contains substring using Polars str.contains()."""
        return operand.str.contains(substring, literal=True)

    def str_starts_with(self, operand: Any, prefix: str) -> pl.Expr:
        """Check if string starts with prefix using Polars str.starts_with()."""
        return operand.str.starts_with(prefix)

    def str_ends_with(self, operand: Any, suffix: str) -> pl.Expr:
        """Check if string ends with suffix using Polars str.ends_with()."""
        return operand.str.ends_with(suffix)

    # ========================================
    # Logical Operations
    # ========================================

    def and_(self, left: Any, right: Any) -> pl.Expr:
        """
        Logical AND operation using Polars & operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing logical AND
        """
        return left & right

    def or_(self, left: Any, right: Any) -> pl.Expr:
        """
        Logical OR operation using Polars | operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing logical OR
        """
        return left | right

    def not_(self, operand: Any) -> pl.Expr:
        """
        Logical NOT operation using Polars ~ operator.

        Args:
            operand: Operand to negate (pl.Expr)

        Returns:
            pl.Expr representing logical NOT
        """
        return ~operand

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(self, element: Any, collection: List[Any]) -> pl.Expr:
        """
        Membership test using Polars is_in() method.

        Args:
            element: Element expression to check (pl.Expr)
            collection: List of values to check against

        Returns:
            pl.Expr representing membership test
        """
        return element.is_in(collection)

    # ========================================
    # Null Operations
    # ========================================

    def is_null(self, operand: Any) -> pl.Expr:
        """
        Check if operand is NULL using Polars is_null() method.

        Args:
            operand: Operand to check (pl.Expr)

        Returns:
            pl.Expr representing null check
        """
        return operand.is_null()

    # ========================================
    # Type Operations
    # ========================================

    def cast(self, value: Any, dtype: Any, **kwargs) -> pl.Expr:
        """
        Cast value to specified type using Polars cast() method.

        Args:
            value: Value expression to cast (pl.Expr)
            dtype: Target data type
            **kwargs: Additional casting options

        Returns:
            pl.Expr representing casted value
        """
        return value.cast(dtype, **kwargs)

    # ========================================
    # Arithmetic Operations
    # ========================================

    def add(self, left: Any, right: Any) -> pl.Expr:
        """
        Addition operation using Polars + operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing addition
        """
        return left + right

    def sub(self, left: Any, right: Any) -> pl.Expr:
        """
        Subtraction operation using Polars - operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing subtraction
        """
        return left - right

    def mul(self, left: Any, right: Any) -> pl.Expr:
        """
        Multiplication operation using Polars * operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing multiplication
        """
        return left * right

    def mod(self, left: Any, right: Any) -> pl.Expr:
        """
        Modulo operation using Polars % operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing modulo
        """
        return left % right

    # ========================================
    # Pattern Matching Operations
    # ========================================

    def pattern_like(self, operand: Any, pattern: str) -> pl.Expr:
        """
        SQL LIKE pattern matching (% and _ wildcards).
        Convert SQL LIKE syntax to regex for Polars.
        """
        # Convert SQL LIKE pattern to regex
        import re
        # Use placeholders for SQL wildcards before escaping (use unique strings without _ or %)
        pattern = pattern.replace('%', '\x00PERCENT\x00').replace('_', '\x00UNDERSCORE\x00')
        # Escape all regex special characters
        regex_pattern = re.escape(pattern)
        # Replace placeholders with regex equivalents
        regex_pattern = regex_pattern.replace('\x00PERCENT\x00', '.*').replace('\x00UNDERSCORE\x00', '.')
        # Anchor the pattern for full match
        regex_pattern = f'^{regex_pattern}$'
        return operand.str.contains(regex_pattern, literal=False)

    def pattern_regex_match(self, operand: Any, pattern: str) -> pl.Expr:
        """
        Check if string fully matches regex pattern.
        """
        # Anchor pattern for full match if not already anchored
        if not pattern.startswith('^'):
            pattern = '^' + pattern
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        return operand.str.contains(pattern, literal=False)

    def pattern_regex_contains(self, operand: Any, pattern: str) -> pl.Expr:
        """
        Check if string contains regex pattern.
        """
        return operand.str.contains(pattern, literal=False)

    def pattern_regex_replace(self, operand: Any, pattern: str, replacement: str) -> pl.Expr:
        """
        Replace text matching regex pattern.
        """
        return operand.str.replace(pattern, replacement, literal=False)

    # ========================================
    # Conditional Operations
    # ========================================

    def conditional_when(self, condition: Any, consequence: Any, alternative: Any) -> pl.Expr:
        """
        Conditional if-then-else using Polars when().then().otherwise().
        """
        return pl.when(condition).then(consequence).otherwise(alternative)

    def conditional_coalesce(self, values: List[Any]) -> pl.Expr:
        """
        Return first non-null value using Polars coalesce().
        """
        return pl.coalesce(values)

    def conditional_fill_null(self, operand: Any, fill_value: Any) -> pl.Expr:
        """
        Replace null values using Polars fill_null().
        """
        return operand.fill_null(fill_value)

    # ========================================
    # Temporal Operations
    # ========================================

    def temporal_year(self, operand: Any) -> pl.Expr:
        """Extract year from datetime using Polars dt.year()."""
        return operand.dt.year()

    def temporal_month(self, operand: Any) -> pl.Expr:
        """Extract month from datetime using Polars dt.month()."""
        return operand.dt.month()

    def temporal_day(self, operand: Any) -> pl.Expr:
        """Extract day from datetime using Polars dt.day()."""
        return operand.dt.day()

    def temporal_hour(self, operand: Any) -> pl.Expr:
        """Extract hour from datetime using Polars dt.hour()."""
        return operand.dt.hour()

    def temporal_minute(self, operand: Any) -> pl.Expr:
        """Extract minute from datetime using Polars dt.minute()."""
        return operand.dt.minute()

    def temporal_second(self, operand: Any) -> pl.Expr:
        """Extract second from datetime using Polars dt.second()."""
        return operand.dt.second()

    def temporal_weekday(self, operand: Any) -> pl.Expr:
        """
        Extract day of week from datetime using Polars dt.weekday() (0=Monday, 6=Sunday).
        Note: Polars returns ISO weekday (1=Monday, 7=Sunday), we convert to 0-6.
        """
        return operand.dt.weekday() - 1

    def temporal_week(self, operand: Any) -> pl.Expr:
        """Extract week number from datetime using Polars dt.week()."""
        return operand.dt.week()

    def temporal_quarter(self, operand: Any) -> pl.Expr:
        """Extract quarter from datetime using Polars dt.quarter()."""
        return operand.dt.quarter()

    def temporal_add_days(self, operand: Any, days: Any) -> pl.Expr:
        """
        Add days to a date using Polars dt.offset_by().

        Args:
            operand: Date/datetime expression
            days: Number of days to add (can be expression or literal)
        """
        # Convert raw values to Polars expressions
        days_expr = pl.lit(days) if not isinstance(days, pl.Expr) else days
        return operand.dt.offset_by(days_expr.cast(pl.Utf8) + pl.lit("d"))

    def temporal_add_months(self, operand: Any, months: Any) -> pl.Expr:
        """
        Add months to a date using Polars dt.offset_by().

        Args:
            operand: Date/datetime expression
            months: Number of months to add (can be expression or literal)
        """
        # Convert raw values to Polars expressions
        months_expr = pl.lit(months) if not isinstance(months, pl.Expr) else months
        return operand.dt.offset_by(months_expr.cast(pl.Utf8) + pl.lit("mo"))

    def temporal_add_years(self, operand: Any, years: Any) -> pl.Expr:
        """
        Add years to a date using Polars dt.offset_by().

        Args:
            operand: Date/datetime expression
            years: Number of years to add (can be expression or literal)
        """
        # Convert raw values to Polars expressions
        years_expr = pl.lit(years) if not isinstance(years, pl.Expr) else years
        return operand.dt.offset_by(years_expr.cast(pl.Utf8) + pl.lit("y"))

    def temporal_diff_days(self, operand: Any, other_date: Any) -> pl.Expr:
        """
        Calculate difference in days between two dates.

        Args:
            operand: First date
            other_date: Second date

        Returns:
            Difference in days (operand - other_date)
        """
        # Subtract dates to get duration, then extract days
        return (operand - other_date).dt.total_days()

    def temporal_add_hours(self, operand: Any, hours: Any) -> pl.Expr:
        """Add hours to a datetime using Polars dt.offset_by()."""
        # Convert raw values to Polars expressions
        hours_expr = pl.lit(hours) if not isinstance(hours, pl.Expr) else hours
        return operand.dt.offset_by(hours_expr.cast(pl.Utf8) + pl.lit("h"))

    def temporal_add_minutes(self, operand: Any, minutes: Any) -> pl.Expr:
        """Add minutes to a datetime using Polars dt.offset_by()."""
        # Convert raw values to Polars expressions
        minutes_expr = pl.lit(minutes) if not isinstance(minutes, pl.Expr) else minutes
        return operand.dt.offset_by(minutes_expr.cast(pl.Utf8) + pl.lit("m"))

    def temporal_add_seconds(self, operand: Any, seconds: Any) -> pl.Expr:
        """Add seconds to a datetime using Polars dt.offset_by()."""
        # Convert raw values to Polars expressions
        seconds_expr = pl.lit(seconds) if not isinstance(seconds, pl.Expr) else seconds
        return operand.dt.offset_by(seconds_expr.cast(pl.Utf8) + pl.lit("s"))

    def temporal_diff_hours(self, operand: Any, other_datetime: Any) -> pl.Expr:
        """Calculate difference in hours between two datetimes."""
        return (operand - other_datetime).dt.total_hours()

    def temporal_diff_minutes(self, operand: Any, other_datetime: Any) -> pl.Expr:
        """Calculate difference in minutes between two datetimes."""
        return (operand - other_datetime).dt.total_minutes()

    def temporal_diff_seconds(self, operand: Any, other_datetime: Any) -> pl.Expr:
        """Calculate difference in seconds between two datetimes."""
        return (operand - other_datetime).dt.total_seconds()

    def temporal_diff_months(self, operand: Any, other_date: Any) -> pl.Expr:
        """
        Calculate difference in months between two dates.
        Note: This is an approximate calculation based on days / 30.
        """
        # Polars doesn't have direct month difference, approximate it
        years_diff = operand.dt.year() - other_date.dt.year()
        months_diff = operand.dt.month() - other_date.dt.month()
        return years_diff * 12 + months_diff

    def temporal_diff_years(self, operand: Any, other_date: Any) -> pl.Expr:
        """Calculate difference in years between two dates."""
        return operand.dt.year() - other_date.dt.year()

    def temporal_truncate(self, operand: Any, unit: Any) -> pl.Expr:
        """
        Truncate datetime to specified unit using Polars dt.truncate().

        Args:
            operand: Datetime expression
            unit: Unit string ('1d', '1h', '1mo', '1y', etc.)
        """
        return operand.dt.truncate(unit)

    def temporal_offset_by(self, operand: Any, offset: Any) -> pl.Expr:
        """
        Add/subtract flexible duration using Polars dt.offset_by().

        Args:
            operand: Datetime expression
            offset: Duration string (e.g., "1d", "2h30m", "-3mo")
        """
        return operand.dt.offset_by(offset)
