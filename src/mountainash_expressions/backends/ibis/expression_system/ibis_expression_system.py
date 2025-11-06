"""Ibis backend implementation of ExpressionSystem."""

from typing import Any, List
import ibis
import ibis.expr.types as ir

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

    def sub(self, left: Any, right: Any) -> ir.Expr:
        """
        Subtraction operation using Ibis - operator.

        Args:
            left: Left operand (ir.Expr)
            right: Right operand (ir.Expr)

        Returns:
            ir.Expr representing subtraction
        """
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
        return left % right

    # ========================================
    # Pattern Matching Operations
    # ========================================

    def pattern_like(self, operand: Any, pattern: str) -> ir.Expr:
        """
        SQL LIKE pattern matching using Ibis like() method.
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
        """
        Add days to a date using Ibis interval.

        Args:
            operand: Date/datetime expression
            days: Number of days to add (can be expression or literal)
        """
        # Create an interval and add to date
        # If days is a literal int, use ibis.interval directly
        # If days is an expression, we need to convert it
        return operand + ibis.interval(days=days)

    def temporal_add_months(self, operand: Any, months: Any) -> ir.Expr:
        """
        Add months to a date using Ibis interval.

        Args:
            operand: Date/datetime expression
            months: Number of months to add (can be expression or literal)
        """
        return operand + ibis.interval(months=months)

    def temporal_add_years(self, operand: Any, years: Any) -> ir.Expr:
        """
        Add years to a date using Ibis interval.

        Args:
            operand: Date/datetime expression
            years: Number of years to add (can be expression or literal)
        """
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
