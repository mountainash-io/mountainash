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
