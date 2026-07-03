"""Filter relation node for row filtering.

Corresponds to Substrait's FilterRel message.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, ClassVar, Optional

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)

from ..reln_base import RelationNode


class FilterRelNode(RelationNode):
    """Row filtering based on a predicate expression.

    Corresponds to Substrait's FilterRel.

    Attributes:
        input: The child relation node
        predicate: The filter expression (ExpressionNode or similar)
    """

    _operation_key: ClassVar[Optional[Enum]] = RKEY_SUBSTRAIT_REL.FILTER

    input: RelationNode
    predicate: Any

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_filter_rel(self)
