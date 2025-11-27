"""Polars native expression operations implementation."""

from typing import Any
import polars as pl

from .base import PolarsBaseExpressionSystem
from ....core.protocols import NativeExpressionProtocol


class PolarsNativeExpressionSystem(PolarsBaseExpressionSystem, NativeExpressionProtocol):
    """Polars implementation of native expression passthrough."""

    def native(self, expr: Any) -> pl.Expr:
        """
        Passthrough for backend-native expressions.

        This allows users to pass Polars expressions directly through
        the expression system without modification.

        Args:
            expr: A native Polars expression (pl.Expr)

        Returns:
            The same expression unchanged

        Raises:
            TypeError: If expr is not a valid Polars expression
        """
        if not isinstance(expr, pl.Expr):
            raise TypeError(
                f"Expected pl.Expr for Polars backend, got {type(expr).__name__}"
            )
        return expr
