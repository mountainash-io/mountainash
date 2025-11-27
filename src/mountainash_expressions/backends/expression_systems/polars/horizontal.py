"""Polars horizontal operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import HorizontalExpressionProtocol


class PolarsHorizontalExpressionSystem(PolarsBaseExpressionSystem, HorizontalExpressionProtocol):
    """Polars implementation of horizontal operations."""

    def coalesce(self, *operands: Any) -> pl.Expr:
        """
        Return the first non-null value from operands.

        Args:
            *operands: Variable number of expressions to evaluate

        Returns:
            The first non-null value
        """
        return pl.coalesce(*operands)

    def greatest(self, *operands: Any) -> pl.Expr:
        """
        Return the maximum value across operands (element-wise).

        Args:
            *operands: Variable number of expressions to compare

        Returns:
            The maximum value for each row
        """
        if len(operands) == 1:
            return operands[0]
        elif len(operands) == 2:
            return pl.max_horizontal(operands[0], operands[1])
        else:
            return pl.max_horizontal(*operands)

    def least(self, *operands: Any) -> pl.Expr:
        """
        Return the minimum value across operands (element-wise).

        Args:
            *operands: Variable number of expressions to compare

        Returns:
            The minimum value for each row
        """
        if len(operands) == 1:
            return operands[0]
        elif len(operands) == 2:
            return pl.min_horizontal(operands[0], operands[1])
        else:
            return pl.min_horizontal(*operands)
