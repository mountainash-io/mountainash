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
