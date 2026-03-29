"""Sort relation node for ordering rows.

Corresponds to Substrait's SortRel message.
"""

from __future__ import annotations
from typing import Any

from mountainash.core.constants import SortField

from ..reln_base import RelationNode


class SortRelNode(RelationNode):
    """Row ordering by one or more sort specifications.

    Corresponds to Substrait's SortRel.

    Attributes:
        input: The child relation node
        sort_fields: List of sort specifications
    """

    input: RelationNode
    sort_fields: list[SortField]

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_sort_rel(self)
