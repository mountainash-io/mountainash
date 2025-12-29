"""Type operations namespace.

Substrait-aligned implementation using CastNode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from .ns_base import BaseExpressionNamespace
from ...expression_nodes import CastNode
from ...expression_system.function_keys.enums import KEY_CAST

if TYPE_CHECKING:
    from ..api_base import BaseExpressionAPI


class CastNamespace(BaseExpressionNamespace):
    """
    Type casting operations namespace.

    Provides type conversion method.

    Methods:
        cast: Cast expression to a different data type
    """

    def cast(
        self,
        dtype: str,
    ) -> BaseExpressionAPI:
        """
        Cast expression to a different data type.

        Args:
            dtype: Target data type (can be string like "int64", "float32", etc.)

        Returns:
            New ExpressionAPI with cast node.
        """
        node = CastNode(
            function_key = KEY_CAST.CAST,
            input=self._node,
            target_type=dtype,
        )
        return self._build(node)
