"""Native expression namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import BaseNamespace
from ..protocols import ENUM_NATIVE_OPERATORS
from ..expression_nodes import NativeExpressionNode

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI


class NativeNamespace(BaseNamespace):
    """
    Native expression passthrough namespace.

    Allows wrapping backend-native expressions in ExpressionAPI.

    Methods:
        native: Wrap a backend-native expression (static method)
    """

    @staticmethod
    def native(expr: Any) -> BaseExpressionAPI:
        """
        Wrap a backend-native expression in ExpressionAPI.

        This allows mixing native backend expressions with the fluent API.

        Args:
            expr: A backend-native expression (pl.Expr, nw.Expr, ibis.Expr, etc.)

        Returns:
            ExpressionAPI wrapping the native expression.

        Example:
            >>> import polars as pl
            >>> native_expr = pl.col("x").filter(pl.col("y") > 5)
            >>> ma_expr = ExpressionBuilder.native(native_expr)
            >>> combined = ma_expr.and_(col("z").eq(10))
        """
        # Import here to avoid circular dependency
        from ..expression_api import BooleanExpressionAPI

        node = NativeExpressionNode(
            ENUM_NATIVE_OPERATORS.NATIVE,
            expr,
        )
        return BooleanExpressionAPI(node)
