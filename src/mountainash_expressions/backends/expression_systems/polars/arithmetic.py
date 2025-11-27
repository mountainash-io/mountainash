"""Polars arithmetic operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import ArithmeticExpressionProtocol


class PolarsArithmeticExpressionSystem(PolarsBaseExpressionSystem, ArithmeticExpressionProtocol):
    """
    Polars implementation of arithmetic operations.

    Implements ArithmeticExpressionProtocol methods.

    Note:
        ISSUE: Deprecated backend had duplicate methods (subtract/sub, multiply/mul, modulo/mod).
        This implementation uses only the full names as specified in the protocol.
    """

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

        Note:
            Deprecated backend also had `sub()` method - removed duplicate.
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

        Note:
            Deprecated backend also had `mul()` method - removed duplicate.
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

        Note:
            Deprecated backend also had `mod()` method - removed duplicate.
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
