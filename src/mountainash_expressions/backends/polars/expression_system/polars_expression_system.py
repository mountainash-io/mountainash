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
