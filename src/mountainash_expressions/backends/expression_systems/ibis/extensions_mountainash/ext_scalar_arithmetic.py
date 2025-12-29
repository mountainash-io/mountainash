"""Ibis ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.mountainash_extensions import (
        ScalarArithmeticExpressionProtocol,
    )

# Type alias for expression type
from mountainash_expressions.types import IbisExpr


class IbisMAExtScalarArithmeticExpressionSystem(IbisBaseExpressionSystem):
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
