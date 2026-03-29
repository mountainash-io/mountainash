"""Aggregate relation node for group-by aggregation.

Corresponds to Substrait's AggregateRel message.
"""

from __future__ import annotations
from typing import Any

from ..reln_base import RelationNode


class AggregateRelNode(RelationNode):
    """Group-by aggregation with keys and measures.

    Corresponds to Substrait's AggregateRel.

    Attributes:
        input: The child relation node
        keys: Grouping key expressions
        measures: Aggregate measure expressions
    """

    input: RelationNode
    keys: list[Any]
    measures: list[Any]

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_aggregate_rel(self)
