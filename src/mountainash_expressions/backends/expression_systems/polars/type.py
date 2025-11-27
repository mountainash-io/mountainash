"""Polars type operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import TypeExpressionProtocol


class PolarsTypeExpressionSystem(PolarsBaseExpressionSystem, TypeExpressionProtocol):
    """
    Polars implementation of type operations.

    Implements TypeExpressionProtocol methods.
    """

    # ========================================
    # Type Operations
    # ========================================

    def cast(self, operand: Any, dtype: Any, **kwargs) -> pl.Expr:
        """
        Cast value to specified type using Polars cast() method.

        Args:
            operand: Value expression to cast (pl.Expr)
            dtype: Target data type
            **kwargs: Additional casting options

        Returns:
            pl.Expr representing casted value
        """
        return operand.cast(dtype, **kwargs)
