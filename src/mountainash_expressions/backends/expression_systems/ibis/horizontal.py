"""Ibis iterable operations implementation."""

from typing import Any
import ibis

from .base import IbisBaseExpressionSystem
from ....core.protocols import IterableExpressionProtocol


class IbisIterableExpressionSystem(IbisBaseExpressionSystem, IterableExpressionProtocol):
    """Ibis implementation of iterable operations."""

    def coalesce(self, *operands: Any) -> Any:
        """
        Return the first non-null value from operands.

        Args:
            *operands: Variable number of expressions to evaluate

        Returns:
            The first non-null value

        Note:
            Ibis uses ibis.coalesce() function.
        """
        return ibis.coalesce(*operands)

    def greatest(self, *operands: Any) -> Any:
        """
        Return the maximum value across operands (element-wise).

        Args:
            *operands: Variable number of expressions to compare

        Returns:
            The maximum value for each row

        Note:
            Ibis uses ibis.greatest() function.
        """
        if len(operands) == 1:
            return operands[0]
        else:
            return ibis.greatest(*operands)

    def least(self, *operands: Any) -> Any:
        """
        Return the minimum value across operands (element-wise).

        Args:
            *operands: Variable number of expressions to compare

        Returns:
            The minimum value for each row

        Note:
            Ibis uses ibis.least() function.
        """
        if len(operands) == 1:
            return operands[0]
        else:
            return ibis.least(*operands)
