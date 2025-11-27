"""Narwhals native expression operations implementation."""

from typing import Any
import narwhals as nw

from .base import NarwhalsBaseExpressionSystem
from ....core.protocols import NativeExpressionProtocol


class NarwhalsNativeExpressionSystem(NarwhalsBaseExpressionSystem, NativeExpressionProtocol):
    """Narwhals implementation of native expression passthrough."""

    def native(self, expr: Any) -> nw.Expr:
        """
        Passthrough for backend-native expressions.

        This allows users to pass Narwhals expressions directly through
        the expression system without modification.

        Args:
            expr: A native Narwhals expression (nw.Expr)

        Returns:
            The same expression unchanged

        Raises:
            TypeError: If expr is not a valid Narwhals expression
        """
        if not isinstance(expr, nw.Expr):
            raise TypeError(
                f"Expected nw.Expr for Narwhals backend, got {type(expr).__name__}"
            )
        return expr
