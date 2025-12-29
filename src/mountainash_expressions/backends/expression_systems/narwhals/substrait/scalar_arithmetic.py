"""Narwhals ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait import (
        ScalarArithmeticExpressionProtocol,
    )

if TYPE_CHECKING:
    from mountainash_expressions.types import NarwhalsExpr


class NarwhalsScalarArithmeticExpressionSystem(NarwhalsBaseExpressionSystem, ScalarArithmeticExpressionProtocol):
    """Narwhals implementation of ScalarArithmeticExpressionProtocol.

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
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Add two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Sum of x and y.
        """
        return x + y

    def subtract(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Subtract y from x.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Difference x - y.
        """
        return x - y

    def multiply(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Multiply two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Product of x and y.
        """
        return x * y

    def divide(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
    ) -> NarwhalsExpr:
        """Divide x by y.

        For integer division, results are truncated toward zero.

        Args:
            x: Dividend.
            y: Divisor.
            overflow: Overflow handling (ignored in Narwhals).
            on_domain_error: Domain error handling (ignored in Narwhals).
            on_division_by_zero: Division by zero handling (ignored in Narwhals).

        Returns:
            Quotient x / y.
        """
        return x / y

    def modulus(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        division_type: Any = None,
        overflow: Any = None,
        on_domain_error: Any = None,
    ) -> NarwhalsExpr:
        """Calculate the remainder when dividing x by y.

        Args:
            x: Dividend.
            y: Divisor.
            division_type: TRUNCATE or FLOOR (Narwhals uses backend default).
            overflow: Overflow handling (ignored in Narwhals).
            on_domain_error: Domain error handling (ignored in Narwhals).

        Returns:
            Remainder of x / y.
        """
        return x % y

    def power(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Raise x to the power of y.

        Args:
            x: Base.
            y: Exponent.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            x raised to the power y.
        """
        return x ** y

    def negate(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Negate a value.

        Args:
            x: Value to negate.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Negated value (-x).
        """
        return -x

    def floor_divide(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Floor division: x // y.

        Divides x by y and returns the floor of the result.

        Args:
            x: Dividend.
            y: Divisor.

        Returns:
            Floor of x / y.
        """
        return x // y
