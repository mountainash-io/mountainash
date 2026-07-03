"""Sort relation node for ordering rows.

Corresponds to Substrait's SortRel message.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, ClassVar, Optional

from mountainash.core.constants import SortField
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)

from ..reln_base import RelationNode


class SortRelNode(RelationNode):
    """Row ordering by one or more sort specifications.

    Corresponds to Substrait's SortRel.

    Attributes:
        input: The child relation node
        sort_fields: List of sort specifications
    """

    _operation_key: ClassVar[Optional[Enum]] = RKEY_SUBSTRAIT_REL.SORT

    input: RelationNode
    sort_fields: list[SortField]

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_sort_rel(self)
