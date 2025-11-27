"""Type operations namespace."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .base import BaseNamespace
from ..protocols import ENUM_TYPE_OPERATORS, TypeBuilderProtocol
from ..expression_nodes import TypeExpressionNode

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ..expression_nodes.base_expression_node import ExpressionNode


class TypeNamespace(BaseNamespace, TypeBuilderProtocol):
    """
    Type casting operations namespace.

    Provides type conversion method.

    Methods:
        cast: Cast expression to a different data type
    """

    def cast(
        self,
        dtype: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """
        Cast expression to a different data type.

        Args:
            dtype: Target data type (can be string like "int64", "float32", etc.)

        Returns:
            New ExpressionAPI with cast node.
        """
        dtype_node = self._to_node_or_value(dtype)
        node = TypeExpressionNode(
            ENUM_TYPE_OPERATORS.CAST,
            self._node,
            dtype_node,
        )
        return self._build(node)
