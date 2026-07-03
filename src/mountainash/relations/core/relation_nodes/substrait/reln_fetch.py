"""Fetch relation node for limit/offset operations.

Corresponds to Substrait's FetchRel message.
"""

from __future__ import annotations
from typing import Any, Optional

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_SUBSTRAIT_REL,
)

from ..reln_base import RelationNode


class FetchRelNode(RelationNode):
    """Limit and offset for result pagination.

    Corresponds to Substrait's FetchRel. Also supports tail
    operations via the from_end flag.

    Attributes:
        input: The child relation node
        offset: Number of rows to skip (default 0)
        count: Maximum number of rows to return (None = unlimited)
        from_end: If True, fetch from the end (tail operation)
    """

    input: RelationNode
    offset: int = 0
    count: Optional[int] = None
    from_end: bool = False

    @property
    def operation_key(self):
        if self.from_end:
            return RKEY_SUBSTRAIT_REL.FETCH_FROM_END
        return RKEY_SUBSTRAIT_REL.FETCH

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_fetch_rel(self)
