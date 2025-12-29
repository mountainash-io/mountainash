"""Polars ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarArithmeticExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr


class PolarsScalarArithmeticExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarArithmeticExpressionSystemProtocol):
    """Polars implementation of ScalarArithmeticExpressionProtocol.

    Implements 7 arithmetic methods:
    - add: Addition
    - subtract: Subtraction
    - multiply: Multiplication
    - divide: Division
    - modulus: Modulo/remainder
    - power: Exponentiation
    - negate: Negation
    """

    def add(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Add two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Sum of x and y.
        """
        return x + y

    def subtract(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Subtract y from x.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Difference x - y.
        """
        return x - y

    def multiply(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Multiply two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Product of x and y.
        """
        return x * y

    def divide(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
    ) -> PolarsExpr:
        """Divide x by y.

        For integer division, results are truncated toward zero.

        Args:
            x: Dividend.
            y: Divisor.
            overflow: Overflow handling (ignored in Polars).
            on_domain_error: Domain error handling (ignored in Polars).
            on_division_by_zero: Division by zero handling (ignored in Polars).

        Returns:
            Quotient x / y.
        """
        return x / y

    def modulus(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        division_type: Any = None,
        overflow: Any = None,
        on_domain_error: Any = None,
    ) -> PolarsExpr:
        """Calculate the remainder when dividing x by y.

        Args:
            x: Dividend.
            y: Divisor.
            division_type: TRUNCATE or FLOOR (Polars uses TRUNCATE by default).
            overflow: Overflow handling (ignored in Polars).
            on_domain_error: Domain error handling (ignored in Polars).

        Returns:
            Remainder of x / y.
        """
        return x % y

    def power(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Raise x to the power of y.

        Args:
            x: Base.
            y: Exponent.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            x raised to the power y.
        """
        return x.pow(y)

    def negate(
        self,
        x: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Negate a value.

        Args:
            x: Value to negate.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Negated value (-x).
        """
        return -x

    def floor_divide(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Floor division: x // y.

        Divides x by y and returns the floor of the result.

        Args:
            x: Dividend.
            y: Divisor.

        Returns:
            Floor of x / y.
        """
        return x // y
