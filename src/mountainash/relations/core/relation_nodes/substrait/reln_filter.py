"""Filter relation node for row filtering.

Corresponds to Substrait's FilterRel message.
"""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode


class FilterRelNode(RelationNode):
    """Row filtering based on a predicate expression.

    Corresponds to Substrait's FilterRel.

    Attributes:
        input: The child relation node
        predicate: The filter expression (ExpressionNode or similar)
    """

    input: RelationNode
    predicate: Any

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_filter_rel(self)
