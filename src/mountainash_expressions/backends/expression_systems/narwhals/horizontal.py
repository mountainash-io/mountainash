"""Narwhals horizontal operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import HorizontalExpressionProtocol


class NarwhalsHorizontalExpressionSystem(NarwhalsBaseExpressionSystem, HorizontalExpressionProtocol):
    """Narwhals implementation of horizontal operations."""

    def coalesce(self, *operands: Any) -> nw.Expr:
        """
        Return the first non-null value from operands.

        Args:
            *operands: Variable number of expressions to evaluate

        Returns:
            The first non-null value
        """
        return nw.coalesce(*operands)

    def greatest(self, *operands: Any) -> nw.Expr:
        """
        Return the maximum value across operands (element-wise).

        Args:
            *operands: Variable number of expressions to compare

        Returns:
            The maximum value for each row

        Note:
            Narwhals uses max_horizontal for element-wise maximum.
        """
        if len(operands) == 1:
            return operands[0]
        else:
            return nw.max_horizontal(*operands)

    def least(self, *operands: Any) -> nw.Expr:
        """
        Return the minimum value across operands (element-wise).

        Args:
            *operands: Variable number of expressions to compare

        Returns:
            The minimum value for each row

        Note:
            Narwhals uses min_horizontal for element-wise minimum.
        """
        if len(operands) == 1:
            return operands[0]
        else:
            return nw.min_horizontal(*operands)
