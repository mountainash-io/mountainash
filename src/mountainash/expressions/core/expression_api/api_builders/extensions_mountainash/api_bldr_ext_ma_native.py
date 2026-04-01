"""Native expression passthrough APIBuilder.

Provides an escape hatch for backend-specific expressions.
"""

from __future__ import annotations


from ..api_builder_base import BaseExpressionAPIBuilder
from ...api_base import BaseExpressionAPI

from mountainash.expressions.core.expression_nodes import LiteralNode
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshNativeAPIBuilderProtocol




class MountainAshNativeAPIBuilder(BaseExpressionAPIBuilder, MountainAshNativeAPIBuilderProtocol):
    """
    Native expression passthrough APIBuilder.

    Provides methods for working with backend-native expressions.
    This is an "escape hatch" that allows mixing backend-specific
    expressions with mountainash expressions.

    IMPORTANT: Native expressions must match the backend of the DataFrame
    they will be used with. A Polars expression cannot be used with an Ibis table.
    """

    def as_native(self) -> BaseExpressionAPI:
        """
        Mark this expression for native passthrough.

        The expression will be passed through unchanged during compilation.
        This is useful when you've already constructed a native expression
        and want to use it within the mountainash API.

        Returns:
            New ExpressionAPI wrapping the current node as native.

        Example:
            >>> import polars as pl
            >>> import mountainash_expressions as ma
            >>>
            >>> # Wrap an existing expression
            >>> expr = ma.col("values").as_native()
        """
        # Wrap current node in a LiteralNode with native dtype
        # The visitor will recognize this and pass through
        node = LiteralNode(value=self._node, dtype="native")
        return self._build(node)
