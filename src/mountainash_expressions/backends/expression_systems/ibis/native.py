"""Ibis native expression operations implementation."""

from typing import Any
from ibis.expr.types import Expr

from .base import IbisBaseExpressionSystem
from ....core.protocols import NativeExpressionProtocol


class IbisNativeExpressionSystem(IbisBaseExpressionSystem, NativeExpressionProtocol):
    """Ibis implementation of native expression passthrough."""

    def native(self, expr: Any) -> Any:
        """
        Passthrough for backend-native expressions.

        This allows users to pass Ibis expressions directly through
        the expression system without modification.

        Args:
            expr: A native Ibis expression (ibis.expr.types.Expr)

        Returns:
            The same expression unchanged

        Raises:
            TypeError: If expr is not a valid Ibis expression
        """
        if not isinstance(expr, Expr):
            raise TypeError(
                f"Expected ibis.expr.types.Expr for Ibis backend, got {type(expr).__name__}"
            )
        return expr
