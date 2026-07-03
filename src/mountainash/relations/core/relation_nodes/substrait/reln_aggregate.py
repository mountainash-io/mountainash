"""Aggregate relation node for group-by aggregation.

Corresponds to Substrait's AggregateRel message.
"""

from __future__ import annotations
from typing import Any

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)

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

    @property
    def operation_key(self):
        if not self.measures:
            return RKEY_SUBSTRAIT_REL.DISTINCT
        return RKEY_SUBSTRAIT_REL.AGGREGATE

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_aggregate_rel(self)
