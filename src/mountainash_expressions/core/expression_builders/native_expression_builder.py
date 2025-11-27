"""Native expression mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import NullBuilderProtocol, ENUM_NULL_OPERATORS
from ..protocols import ENUM_NATIVE_OPERATORS, NativeBuilderProtocol
from ..expression_nodes import NativeExpressionNode


class NativeExpressionBuilder(BaseExpressionBuilder, NativeBuilderProtocol):
    """
    Mixin providing native expression passthrough for ExpressionBuilder.

    Allows wrapping backend-native expressions in ExpressionBuilder.
    Note: NativeBuilderProtocol doesn't define methods - this is just for consistency.
    """


    @staticmethod
    def native(expr: Any) -> BaseExpressionBuilder:
        """
        Wrap a backend-native expression in ExpressionBuilder.

        This allows mixing native backend expressions with the fluent API.

        Args:
            expr: A backend-native expression (pl.Expr, nw.Expr, ibis.Expr, etc.)

        Returns:
            ExpressionBuilder wrapping the native expression

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
            expr
        )
        return BooleanExpressionAPI(node)
