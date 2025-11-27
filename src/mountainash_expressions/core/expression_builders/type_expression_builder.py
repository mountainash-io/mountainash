"""Type operations mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import TypeBuilderProtocol, ENUM_TYPE_OPERATORS
from ..expression_nodes import TypeExpressionNode


class TypeExpressionBuilder(BaseExpressionBuilder, TypeBuilderProtocol):
    """
    Mixin providing type casting operations for ExpressionBuilder.

    Implements TypeBuilderProtocol with a single method: cast().
    """

    def cast(self, dtype: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Cast expression to a different data type.

        Args:
            dtype: Target data type (can be string like "int64", "float32", etc.)

        Returns:
            New ExpressionBuilder with cast node

        Example:
            >>> col("age").cast("int64")
            >>> col("price").cast("float32")
        """
        dtype_node = self._to_node_or_value(dtype)
        node = TypeExpressionNode(
            ENUM_TYPE_OPERATORS.CAST,
            self._node,
            dtype_node
        )
        return self.create(node)
