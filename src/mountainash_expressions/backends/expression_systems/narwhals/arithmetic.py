"""Narwhals arithmetic operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import ArithmeticExpressionProtocol


class NarwhalsArithmeticExpressionSystem(NarwhalsBaseExpressionSystem, ArithmeticExpressionProtocol):
    """
    Narwhals implementation of arithmetic operations.

    Implements ArithmeticExpressionProtocol methods.

    Note:
        ISSUE: Deprecated backend had duplicate methods (subtract/sub, multiply/mul, modulo/mod).
        This implementation uses only the full names as specified in the protocol.
    """

    # ========================================
    # Arithmetic Operations
    # ========================================

    def add(self, left: Any, right: Any) -> nw.Expr:
        """Addition operation using Narwhals + operator."""
        return left + right

    def subtract(self, left: Any, right: Any) -> nw.Expr:
        """
        Subtraction operation using Narwhals - operator.

        Note:
            Deprecated backend also had `sub()` method - removed duplicate.
        """
        return left - right

    def multiply(self, left: Any, right: Any) -> nw.Expr:
        """
        Multiplication operation using Narwhals * operator.

        Note:
            Deprecated backend also had `mul()` method - removed duplicate.
        """
        return left * right

    def divide(self, left: Any, right: Any) -> nw.Expr:
        """Division operation using Narwhals / operator."""
        return left / right

    def modulo(self, left: Any, right: Any) -> nw.Expr:
        """
        Modulo operation using Narwhals % operator.

        Note:
            Deprecated backend also had `mod()` method - removed duplicate.
        """
        return left % right

    def power(self, left: Any, right: Any) -> nw.Expr:
        """Exponentiation operation using Narwhals ** operator."""
        return left ** right

    def floor_divide(self, left: Any, right: Any) -> nw.Expr:
        """Floor division operation using Narwhals // operator."""
        return left // right
