"""Narwhals ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from .base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait.prtcl_scalar_arithmetic import (
        ScalarArithmeticExpressionProtocol,
    )

# Type alias for expression type
SupportedExpressions = nw.Expr


class NarwhalsScalarArithmeticSystem(NarwhalsBaseExpressionSystem):
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
        x: SupportedExpressions,
        y: SupportedExpressions,
        /,
        overflow: Any = None,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        y: SupportedExpressions,
        /,
        overflow: Any = None,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        y: SupportedExpressions,
        /,
        overflow: Any = None,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        y: SupportedExpressions,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        y: SupportedExpressions,
        /,
        division_type: Any = None,
        overflow: Any = None,
        on_domain_error: Any = None,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        y: SupportedExpressions,
        /,
        overflow: Any = None,
    ) -> SupportedExpressions:
        """Raise x to the power of y.

        Args:
            x: Base.
            y: Exponent.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            x raised to the power y.
        """
        return x.pow(y)

    def negate(
        self,
        x: SupportedExpressions,
        /,
        overflow: Any = None,
    ) -> SupportedExpressions:
        """Negate a value.

        Args:
            x: Value to negate.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Negated value (-x).
        """
        return -x
