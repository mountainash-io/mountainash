"""Narwhals backend implementation of ExpressionSystem."""

from typing import Any, List
import narwhals as nw

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS


class NarwhalsExpressionSystem(ExpressionSystem):
    """
    Narwhals-specific implementation of ExpressionSystem.

    This class encapsulates all Narwhals-specific operations,
    allowing visitors to build expressions without direct knowledge
    of the Narwhals API.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return Narwhals backend type."""
        return CONST_VISITOR_BACKENDS.NARWHALS

    # ========================================
    # Core Primitives
    # ========================================

    def col(self, name: str, **kwargs) -> nw.Expr:
        """
        Create a Narwhals column reference expression.

        Args:
            name: Column name
            **kwargs: Additional options for nw.col()

        Returns:
            nw.Expr representing the column reference
        """
        return nw.col(name, **kwargs)

    def lit(self, value: Any) -> nw.Expr:
        """
        Create a Narwhals literal value expression.

        Args:
            value: The literal value (int, float, str, bool, etc.)

        Returns:
            nw.Expr representing the literal value
        """
        return nw.lit(value)

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(self, left: Any, right: Any) -> nw.Expr:
        """
        Equality comparison using Narwhals operator overloading.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing equality comparison
        """
        return left == right

    def ne(self, left: Any, right: Any) -> nw.Expr:
        """
        Inequality comparison using Narwhals operator overloading.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing inequality comparison
        """
        return left != right

    def gt(self, left: Any, right: Any) -> nw.Expr:
        """
        Greater-than comparison using Narwhals operator overloading.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing greater-than comparison
        """
        return left > right

    def lt(self, left: Any, right: Any) -> nw.Expr:
        """
        Less-than comparison using Narwhals operator overloading.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing less-than comparison
        """
        return left < right

    def ge(self, left: Any, right: Any) -> nw.Expr:
        """
        Greater-than-or-equal comparison using Narwhals operator overloading.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing greater-than-or-equal comparison
        """
        return left >= right

    def le(self, left: Any, right: Any) -> nw.Expr:
        """
        Less-than-or-equal comparison using Narwhals operator overloading.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing less-than-or-equal comparison
        """
        return left <= right

    # ========================================
    # Arithmetic Operations
    # ========================================

    def add(self, left: Any, right: Any) -> nw.Expr:
        """
        Addition operation using Narwhals + operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing addition
        """
        return left + right

    def subtract(self, left: Any, right: Any) -> nw.Expr:
        """
        Subtraction operation using Narwhals - operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing subtraction
        """
        return left - right

    def multiply(self, left: Any, right: Any) -> nw.Expr:
        """
        Multiplication operation using Narwhals * operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing multiplication
        """
        return left * right

    def divide(self, left: Any, right: Any) -> nw.Expr:
        """
        Division operation using Narwhals / operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing division
        """
        return left / right

    def modulo(self, left: Any, right: Any) -> nw.Expr:
        """
        Modulo operation using Narwhals % operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing modulo
        """
        return left % right

    def power(self, left: Any, right: Any) -> nw.Expr:
        """
        Exponentiation operation using Narwhals ** operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing exponentiation
        """
        return left ** right

    def floor_divide(self, left: Any, right: Any) -> nw.Expr:
        """
        Floor division operation using Narwhals // operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing floor division
        """
        return left // right

    # ========================================
    # String Operations
    # ========================================

    def str_upper(self, operand: Any) -> nw.Expr:
        """Convert string to uppercase using Narwhals str.to_uppercase()."""
        return operand.str.to_uppercase()

    def str_lower(self, operand: Any) -> nw.Expr:
        """Convert string to lowercase using Narwhals str.to_lowercase()."""
        return operand.str.to_lowercase()

    def str_trim(self, operand: Any) -> nw.Expr:
        """Trim whitespace from both sides using Narwhals str.strip_chars()."""
        return operand.str.strip_chars()

    def str_ltrim(self, operand: Any) -> nw.Expr:
        """Trim whitespace from left side using Narwhals str.strip_chars_start()."""
        return operand.str.strip_chars_start()

    def str_rtrim(self, operand: Any) -> nw.Expr:
        """Trim whitespace from right side using Narwhals str.strip_chars_end()."""
        return operand.str.strip_chars_end()

    def str_substring(self, operand: Any, start: int, length: int = None) -> nw.Expr:
        """Extract substring using Narwhals str.slice()."""
        if length is None:
            # From start to end
            return operand.str.slice(start)
        else:
            # From start with specific length
            return operand.str.slice(start, length)

    def str_concat(self, operand: Any, *others: Any, separator: str = "") -> nw.Expr:
        """Concatenate strings. Note: Narwhals uses + operator for concat."""
        result = operand
        for other in others:
            if separator:
                result = result + self.lit(separator) + other
            else:
                result = result + other
        return result

    def str_length(self, operand: Any) -> nw.Expr:
        """Get string length using Narwhals str.len_chars()."""
        return operand.str.len_chars()

    def str_replace(self, operand: Any, old: str, new: str) -> nw.Expr:
        """Replace substring using Narwhals str.replace()."""
        return operand.str.replace(old, new)

    def str_contains(self, operand: Any, substring: str) -> nw.Expr:
        """Check if string contains substring using Narwhals str.contains()."""
        return operand.str.contains(substring)

    def str_starts_with(self, operand: Any, prefix: str) -> nw.Expr:
        """Check if string starts with prefix using Narwhals str.starts_with()."""
        return operand.str.starts_with(prefix)

    def str_ends_with(self, operand: Any, suffix: str) -> nw.Expr:
        """Check if string ends with suffix using Narwhals str.ends_with()."""
        return operand.str.ends_with(suffix)

    # ========================================
    # Logical Operations
    # ========================================

    def and_(self, left: Any, right: Any) -> nw.Expr:
        """
        Logical AND operation using Narwhals & operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing logical AND
        """
        return left & right

    def or_(self, left: Any, right: Any) -> nw.Expr:
        """
        Logical OR operation using Narwhals | operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing logical OR
        """
        return left | right

    def not_(self, operand: Any) -> nw.Expr:
        """
        Logical NOT operation using Narwhals ~ operator.

        Args:
            operand: Operand to negate (nw.Expr)

        Returns:
            nw.Expr representing logical NOT
        """
        return ~operand

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(self, element: Any, collection: List[Any]) -> nw.Expr:
        """
        Membership test using Narwhals is_in() method.

        Args:
            element: Element expression to check (nw.Expr)
            collection: List of values to check against

        Returns:
            nw.Expr representing membership test
        """
        return element.is_in(collection)

    # ========================================
    # Null Operations
    # ========================================

    def is_null(self, operand: Any) -> nw.Expr:
        """
        Check if operand is NULL using Narwhals is_null() method.

        Args:
            operand: Operand to check (nw.Expr)

        Returns:
            nw.Expr representing null check
        """
        return operand.is_null()

    # ========================================
    # Type Operations
    # ========================================

    def cast(self, value: Any, dtype: Any, **kwargs) -> nw.Expr:
        """
        Cast value to specified type using Narwhals cast() method.

        Args:
            value: Value expression to cast (nw.Expr)
            dtype: Target data type
            **kwargs: Additional casting options

        Returns:
            nw.Expr representing casted value
        """
        return value.cast(dtype, **kwargs)

    # ========================================
    # Arithmetic Operations
    # ========================================

    def add(self, left: Any, right: Any) -> nw.Expr:
        """
        Addition operation using Narwhals + operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing addition
        """
        return left + right

    def sub(self, left: Any, right: Any) -> nw.Expr:
        """
        Subtraction operation using Narwhals - operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing subtraction
        """
        return left - right

    def mul(self, left: Any, right: Any) -> nw.Expr:
        """
        Multiplication operation using Narwhals * operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing multiplication
        """
        return left * right

    def mod(self, left: Any, right: Any) -> nw.Expr:
        """
        Modulo operation using Narwhals % operator.

        Args:
            left: Left operand (nw.Expr)
            right: Right operand (nw.Expr)

        Returns:
            nw.Expr representing modulo
        """
        return left % right

    # ========================================
    # Pattern Matching Operations
    # ========================================

    def pattern_like(self, operand: Any, pattern: str) -> nw.Expr:
        """
        SQL LIKE pattern matching (% and _ wildcards).
        Convert SQL LIKE syntax to regex for Narwhals.
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
        return operand.str.contains(regex_pattern)

    def pattern_regex_match(self, operand: Any, pattern: str) -> nw.Expr:
        """
        Check if string fully matches regex pattern.
        """
        # Anchor pattern for full match if not already anchored
        if not pattern.startswith('^'):
            pattern = '^' + pattern
        if not pattern.endswith('$'):
            pattern = pattern + '$'
        return operand.str.contains(pattern)

    def pattern_regex_contains(self, operand: Any, pattern: str) -> nw.Expr:
        """
        Check if string contains regex pattern.
        """
        return operand.str.contains(pattern)

    def pattern_regex_replace(self, operand: Any, pattern: str, replacement: str) -> nw.Expr:
        """
        Replace text matching regex pattern.
        """
        return operand.str.replace(pattern, replacement)

    # ========================================
    # Conditional Operations
    # ========================================

    def conditional_when(self, condition: Any, consequence: Any, alternative: Any) -> nw.Expr:
        """
        Conditional if-then-else using Narwhals when().then().otherwise().
        """
        return nw.when(condition).then(consequence).otherwise(alternative)

    def conditional_coalesce(self, values: List[Any]) -> nw.Expr:
        """
        Return first non-null value using Narwhals coalesce().
        """
        return nw.coalesce(values)

    def conditional_fill_null(self, operand: Any, fill_value: Any) -> nw.Expr:
        """
        Replace null values using Narwhals fill_null().
        """
        return operand.fill_null(fill_value)

    # ========================================
    # Temporal Operations
    # ========================================

    def temporal_year(self, operand: Any) -> nw.Expr:
        """Extract year from datetime using Narwhals dt.year()."""
        return operand.dt.year()

    def temporal_month(self, operand: Any) -> nw.Expr:
        """Extract month from datetime using Narwhals dt.month()."""
        return operand.dt.month()

    def temporal_day(self, operand: Any) -> nw.Expr:
        """Extract day from datetime using Narwhals dt.day()."""
        return operand.dt.day()

    def temporal_hour(self, operand: Any) -> nw.Expr:
        """Extract hour from datetime using Narwhals dt.hour()."""
        return operand.dt.hour()

    def temporal_minute(self, operand: Any) -> nw.Expr:
        """Extract minute from datetime using Narwhals dt.minute()."""
        return operand.dt.minute()

    def temporal_second(self, operand: Any) -> nw.Expr:
        """Extract second from datetime using Narwhals dt.second()."""
        return operand.dt.second()

    def temporal_weekday(self, operand: Any) -> nw.Expr:
        """
        Extract day of week from datetime using Narwhals dt.weekday() (0=Monday, 6=Sunday).
        Note: Narwhals returns ISO weekday (1=Monday, 7=Sunday), we convert to 0-6.
        """
        return operand.dt.weekday() - 1

    def temporal_week(self, operand: Any) -> nw.Expr:
        """Extract week number from datetime using Narwhals dt.week()."""
        # Note: Narwhals may use dt.week() or dt.iso_week()
        return operand.dt.week() if hasattr(operand.dt, 'week') else operand.dt.iso_week()

    def temporal_quarter(self, operand: Any) -> nw.Expr:
        """
        Extract quarter from datetime.
        Note: Narwhals may not have dt.quarter(), so we calculate from month.
        """
        if hasattr(operand.dt, 'quarter'):
            return operand.dt.quarter()
        else:
            # Calculate quarter from month: Q1(1-3), Q2(4-6), Q3(7-9), Q4(10-12)
            # Formula: (month - 1) // 3 + 1
            month = operand.dt.month()
            return ((month - 1) // 3 + 1)

    def temporal_add_days(self, operand: Any, days: Any) -> nw.Expr:
        """
        Add days to a date using Narwhals dt.offset_by().

        Args:
            operand: Date/datetime expression
            days: Number of days to add (can be expression or literal)
        """
        # Convert days to duration string format
        return operand.dt.offset_by(days.cast(nw.String) + nw.lit("d"))

    def temporal_add_months(self, operand: Any, months: Any) -> nw.Expr:
        """
        Add months to a date using Narwhals dt.offset_by().

        Args:
            operand: Date/datetime expression
            months: Number of months to add (can be expression or literal)
        """
        return operand.dt.offset_by(months.cast(nw.String) + nw.lit("mo"))

    def temporal_add_years(self, operand: Any, years: Any) -> nw.Expr:
        """
        Add years to a date using Narwhals dt.offset_by().

        Args:
            operand: Date/datetime expression
            years: Number of years to add (can be expression or literal)
        """
        return operand.dt.offset_by(years.cast(nw.String) + nw.lit("y"))

    def temporal_diff_days(self, operand: Any, other_date: Any) -> nw.Expr:
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
