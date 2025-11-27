"""Polars boolean operations implementation."""

from typing import Any, List, Optional
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import BooleanExpressionProtocol


class PolarsBooleanExpressionSystem(PolarsBaseExpressionSystem, BooleanExpressionProtocol):
    """
    Polars implementation of boolean operations.

    Implements BooleanExpressionProtocol methods.
    """

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

    def is_close(self, left: Any, right: Any, precision: Optional[float] = None) -> pl.Expr:
        """
        Approximate equality comparison.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)
            precision: Tolerance for comparison (default: 1e-5)

        Returns:
            pl.Expr representing approximate equality

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Using absolute difference approach.
        """
        if precision is None:
            precision = 1e-5

        # Check if absolute difference is within tolerance
        return (left - right).abs() <= pl.lit(precision)

    def between(self, value: Any, lower: Any, upper: Any, closed: Optional[str] = "both") -> pl.Expr:
        """
        Check if value is between bounds.

        Args:
            value: Value to check (pl.Expr)
            lower: Lower bound (pl.Expr)
            upper: Upper bound (pl.Expr)
            closed: Which bounds are inclusive - "left", "right", "both", "neither"

        Returns:
            pl.Expr representing range check

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Implementation based on Polars is_between() method.
        """
        return value.is_between(lower, upper, closed=closed)

    # ========================================
    # Logical Operations (Binary)
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

    def xor_(self, left: Any, right: Any) -> pl.Expr:
        """
        Logical XOR operation using Polars ^ operator.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing logical XOR

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Using Polars ^ operator for boolean XOR.
        """
        return left ^ right

    def xor_parity(self, left: Any, right: Any) -> pl.Expr:
        """
        Parity XOR - same as regular XOR for binary case.

        Args:
            left: Left operand (pl.Expr)
            right: Right operand (pl.Expr)

        Returns:
            pl.Expr representing parity XOR

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            For binary operands, XOR parity is same as XOR.
            The visitor handles multi-operand case using reduce.
        """
        return left ^ right

    # ========================================
    # Logical Operations (Unary)
    # ========================================

    def not_(self, operand: Any) -> pl.Expr:
        """
        Logical NOT operation using Polars ~ operator.

        Args:
            operand: Operand to negate (pl.Expr)

        Returns:
            pl.Expr representing logical NOT
        """
        return ~operand

    def is_true(self, operand: Any) -> pl.Expr:
        """
        Check if operand is explicitly True.

        Args:
            operand: Operand to check (pl.Expr)

        Returns:
            pl.Expr checking if operand is True

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Simple equality check with True literal.
        """
        return operand == pl.lit(True)

    def is_false(self, operand: Any) -> pl.Expr:
        """
        Check if operand is explicitly False.

        Args:
            operand: Operand to check (pl.Expr)

        Returns:
            pl.Expr checking if operand is False

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Simple equality check with False literal.
        """
        return operand == pl.lit(False)

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

    def is_not_in(self, element: Any, collection: List[Any]) -> pl.Expr:
        """
        Negative membership test.

        Args:
            element: Element expression to check (pl.Expr)
            collection: List of values to check against

        Returns:
            pl.Expr representing negative membership test

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Implementing as negation of is_in.
        """
        return ~element.is_in(collection)

    # ========================================
    # Constant Operations
    # ========================================

    def always_true(self) -> pl.Expr:
        """
        Return a literal True expression.

        Returns:
            pl.Expr representing constant True

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Simple True literal.
        """
        return pl.lit(True)

    def always_false(self) -> pl.Expr:
        """
        Return a literal False expression.

        Returns:
            pl.Expr representing constant False

        Note:
            ISSUE: Protocol specifies this but deprecated backend doesn't implement it.
            Simple False literal.
        """
        return pl.lit(False)
