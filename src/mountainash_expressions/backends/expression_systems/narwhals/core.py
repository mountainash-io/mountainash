"""Narwhals core operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import CoreExpressionProtocol


class NarwhalsCoreExpressionSystem(NarwhalsBaseExpressionSystem,
                                     CoreExpressionProtocol):
    """
    Narwhals implementation of core operations.

    Implements CoreExpressionProtocol methods.
    """

    # ========================================
    # Core Primitives
    # ========================================

    def col(self, name: str, **kwargs) -> nw.Expr:
        """
        Create a Narwhals column reference expression.

        Args:
            name: Column name
            **kwargs: Additional options for nw.col()

        Returns:
            nw.Expr representing the column reference
        """
        return nw.col(name, **kwargs)

    def lit(self, value: Any) -> nw.Expr:
        """
        Create a Narwhals literal value expression.

        Args:
            value: The literal value (int, float, str, bool, etc.)

        Returns:
            nw.Expr representing the literal value
        """
        return nw.lit(value)
