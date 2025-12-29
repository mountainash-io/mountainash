"""Ibis ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait import (
        ScalarArithmeticExpressionProtocol,
    )

# Type alias for expression type
from mountainash_expressions.types import IbisExpr


class IbisScalarArithmeticExpressionSystem(IbisBaseExpressionSystem, ScalarArithmeticExpressionProtocol):
    """Ibis implementation of ScalarArithmeticExpressionProtocol.

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
        x: IbisExpr,
        y: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
        """Add two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Sum of x and y.
        """
        return x + y

    def subtract(
        self,
        x: IbisExpr,
        y: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
        """Subtract y from x.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Difference x - y.
        """
        return x - y

    def multiply(
        self,
        x: IbisExpr,
        y: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
        """Multiply two values.

        Args:
            x: First operand.
            y: Second operand.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Product of x and y.
        """
        return x * y

    def divide(
        self,
        x: IbisExpr,
        y: IbisExpr,
        /,
        overflow: Any = None,
        on_domain_error: Any = None,
        on_division_by_zero: Any = None,
    ) -> IbisExpr:
        """Divide x by y.

        For integer division, results are truncated toward zero.

        Args:
            x: Dividend.
            y: Divisor.
            overflow: Overflow handling (ignored in Ibis).
            on_domain_error: Domain error handling (ignored in Ibis).
            on_division_by_zero: Division by zero handling (ignored in Ibis).

        Returns:
            Quotient x / y.
        """
        return x / y

    def modulus(
        self,
        x: IbisExpr,
        y: IbisExpr,
        /,
        division_type: Any = None,
        overflow: Any = None,
        on_domain_error: Any = None,
    ) -> IbisExpr:
        """Calculate the remainder when dividing x by y.

        Args:
            x: Dividend.
            y: Divisor.
            division_type: TRUNCATE or FLOOR (Ibis uses backend default).
            overflow: Overflow handling (ignored in Ibis).
            on_domain_error: Domain error handling (ignored in Ibis).

        Returns:
            Remainder of x / y.
        """
        return x % y

    def power(
        self,
        x: IbisExpr,
        y: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
        """Raise x to the power of y.

        Args:
            x: Base.
            y: Exponent.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            x raised to the power y.
        """
        return x.pow(y)

    def negate(
        self,
        x: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
        """Negate a value.

        Args:
            x: Value to negate.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Negated value (-x).
        """
        return -x

    def floor_divide(
        self,
        x: IbisExpr,
        y: IbisExpr,
        /,
    ) -> IbisExpr:
        """Floor division: x // y.

        Divides x by y and returns the floor of the result.

        Args:
            x: Dividend.
            y: Divisor.

        Returns:
            Floor of x / y.
        """
        return x // y
