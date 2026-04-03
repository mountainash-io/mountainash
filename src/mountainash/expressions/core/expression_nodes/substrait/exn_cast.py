"""Cast node for type conversions.

Corresponds to Substrait's Cast message.
"""

from __future__ import annotations
from typing import Any, Literal

from .exn_base import ExpressionNode


class CastNode(ExpressionNode):
    """A type conversion/cast expression.

    Represents converting an expression from one type to another.

    Attributes:
        input: The expression to cast
        target_type: The target data type (e.g., "i32", "fp64", "string", "date")
        failure_behavior: How to handle cast failures:
            - "throw": Raise an error on invalid conversion (default)
            - "null": Return NULL on invalid conversion

    Examples:
        >>> CastNode(input=col_node, target_type="i64")
        >>> CastNode(input=str_node, target_type="date", failure_behavior="null")
    """

    input: ExpressionNode
    target_type: str
    failure_behavior: Literal["throw", "null"] = "throw"

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_cast(self)
