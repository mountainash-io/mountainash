"""Narwhals ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarArithmeticExpressionSystemProtocol


if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class MountainAshNarwhalsScalarArithmeticExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarArithmeticExpressionSystemProtocol):
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
