"""Set relation node for union/intersect/except operations.

Corresponds to Substrait's SetRel message.
"""

from __future__ import annotations
from typing import Any

from mountainash.core.constants import SetType

from ..reln_base import RelationNode


class SetRelNode(RelationNode):
    """Set operations combining multiple relations.

    Corresponds to Substrait's SetRel.

    Attributes:
        inputs: List of child relation nodes to combine
        set_type: The set operation type (UNION_ALL, UNION_DISTINCT)
    """

    inputs: list[RelationNode]
    set_type: SetType

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_set_rel(self)
