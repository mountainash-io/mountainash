"""Narwhals boolean operations implementation."""

from typing import Any, List, Optional
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import BooleanExpressionProtocol


class NarwhalsBooleanExpressionSystem(NarwhalsBaseExpressionSystem, BooleanExpressionProtocol):
    """
    Narwhals implementation of boolean operations.

    Implements BooleanExpressionProtocol methods.
    """

    # ========================================
    # Comparison Operations
    # ========================================

    def eq(self, left: Any, right: Any) -> nw.Expr:
        """Equality comparison using Narwhals operator overloading."""
        return left == right

    def ne(self, left: Any, right: Any) -> nw.Expr:
        """Inequality comparison using Narwhals operator overloading."""
        return left != right

    def gt(self, left: Any, right: Any) -> nw.Expr:
        """Greater-than comparison using Narwhals operator overloading."""
        return left > right

    def lt(self, left: Any, right: Any) -> nw.Expr:
        """Less-than comparison using Narwhals operator overloading."""
        return left < right

    def ge(self, left: Any, right: Any) -> nw.Expr:
        """Greater-than-or-equal comparison using Narwhals operator overloading."""
        return left >= right

    def le(self, left: Any, right: Any) -> nw.Expr:
        """Less-than-or-equal comparison using Narwhals operator overloading."""
        return left <= right

    def is_close(self, left: Any, right: Any, precision: Optional[float] = None) -> nw.Expr:
        """
        Approximate equality comparison.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Using absolute difference approach.
        """
        if precision is None:
            precision = 1e-5
        return (left - right).abs() <= nw.lit(precision)

    def between(self, value: Any, lower: Any, upper: Any, closed: Optional[str] = "both") -> nw.Expr:
        """
        Check if value is between bounds.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Narwhals supports is_between() method.
        """
        return value.is_between(lower, upper, closed=closed)

    # ========================================
    # Logical Operations (Binary)
    # ========================================

    def and_(self, left: Any, right: Any) -> nw.Expr:
        """Logical AND operation using Narwhals & operator."""
        return left & right

    def or_(self, left: Any, right: Any) -> nw.Expr:
        """Logical OR operation using Narwhals | operator."""
        return left | right

    def xor_(self, left: Any, right: Any) -> nw.Expr:
        """
        Logical XOR operation using Narwhals ^ operator.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return left ^ right

    def xor_parity(self, left: Any, right: Any) -> nw.Expr:
        """
        Parity XOR - same as regular XOR for binary case.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return left ^ right

    # ========================================
    # Logical Operations (Unary)
    # ========================================

    def not_(self, operand: Any) -> nw.Expr:
        """Logical NOT operation using Narwhals ~ operator."""
        return ~operand

    def is_true(self, operand: Any) -> nw.Expr:
        """
        Check if operand is explicitly True.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return operand == nw.lit(True)

    def is_false(self, operand: Any) -> nw.Expr:
        """
        Check if operand is explicitly False.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return operand == nw.lit(False)

    # ========================================
    # Collection Operations
    # ========================================

    def is_in(self, element: Any, collection: List[Any]) -> nw.Expr:
        """Membership test using Narwhals is_in() method."""
        return element.is_in(collection)

    def is_not_in(self, element: Any, collection: List[Any]) -> nw.Expr:
        """
        Negative membership test.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return ~element.is_in(collection)

    # ========================================
    # Constant Operations
    # ========================================

    def always_true(self) -> nw.Expr:
        """
        Return a literal True expression.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return nw.lit(True)

    def always_false(self) -> nw.Expr:
        """
        Return a literal False expression.

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
        """
        return nw.lit(False)
