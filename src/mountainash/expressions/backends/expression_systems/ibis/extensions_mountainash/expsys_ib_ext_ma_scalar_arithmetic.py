"""Ibis ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarArithmeticExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisNumericExpr



class MountainAshIbisScalarArithmeticExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarArithmeticExpressionSystemProtocol["IbisNumericExpr"]):
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

    def floor_divide(
        self,
        x: IbisNumericExpr,
        y: IbisNumericExpr,
        /,
    ) -> IbisNumericExpr:
        """Floor division: x // y.

        Divides x by y and returns the floor of the result.

        Args:
            x: Dividend.
            y: Divisor.

        Returns:
            Floor of x / y.
        """
        return x // y
