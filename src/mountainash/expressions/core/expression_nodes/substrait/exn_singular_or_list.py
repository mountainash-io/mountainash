"""Singular-or-list node for IN operator.

Corresponds to Substrait's SingularOrList message.
"""

from __future__ import annotations
from typing import Any, List

from .exn_base import ExpressionNode


class SingularOrListNode(ExpressionNode):
    """A singular-or-list expression for membership tests.

    Represents the IN operator: value IN (options...).
    This is one of Substrait's 6 core expression types.

    Used for:
    - is_in() operations: col("status").is_in("active", "pending")
    - is_not_in() operations (negated): NOT (value IN options)
    - index_in() operations: return position in list

    Attributes:
        value: The expression to check membership for.
        options: List of expressions to check against.

    Examples:
        >>> # Check if status is in list
        >>> SingularOrListNode(
        ...     value=FieldReferenceNode(field="status"),
        ...     options=[LiteralNode(value="active"), LiteralNode(value="pending")]
        ... )
    """

    value: ExpressionNode
    options: List[ExpressionNode]

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_singular_or_list(self)
