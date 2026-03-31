"""Polars ScalarArithmeticExpressionProtocol implementation.

Implements arithmetic operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarArithmeticExpressionSystemProtocol


# Type alias for expression type
if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class MountainAshPolarsScalarArithmeticExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarArithmeticExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of ScalarArithmeticExpressionProtocol.

    Implements 1 arithmetic methods:
    - floor_divide: Floor Division
    """


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
