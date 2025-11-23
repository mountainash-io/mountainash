
from __future__ import annotations
from typing import Any, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode


class ExpressionBuilder:
    """
    Fluent API builder for expressions.

    This class provides a chainable interface for building expressions
    that follows the Polars/Narwhals pattern. Under the hood, it builds
    an ExpressionNode AST that can be compiled to any backend.

    Example:
        >>> expr = ExpressionBuilder.col("age").gt(30)
        >>> backend_expr = expr.compile(df)
    """

    def __init__(self, node: Union[ExpressionNode, Any]):
        """
        Initialize with an ExpressionNode or raw value.

        Args:
            node: The underlying expression node or raw value (string, int, etc.)
        """
        self._node = node

    @property
    def node(self) -> Union[ExpressionNode, Any]:
        """Get the underlying expression node or raw value."""
        return self._node


    # ========================================
    # Helper Methods
    # ========================================

    def _to_node(self, other: Union[ExpressionBuilder, Any]) -> Any:
        """
        Convert value to node representation.

        Args:
            other: ExpressionBuilder, ExpressionNode, or raw value

        Returns:
            Node representation (ExpressionNode or raw value)

        Note:
            Raw values (strings, ints, etc.) are kept as-is.
            The visitor's _process_operand() will handle converting them.
        """
        if isinstance(other, ExpressionBuilder):
            return other._node
        else:
            # Keep raw values as-is (visitor will handle them)
            return other
