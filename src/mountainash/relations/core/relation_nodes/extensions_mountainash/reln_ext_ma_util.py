"""Extension relation node for mountainash-specific operations.

These operations are not part of the Substrait specification but are
needed for practical DataFrame manipulation.
"""

from __future__ import annotations
from typing import Any

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)

from ..reln_base import RelationNode


class ExtensionRelNode(RelationNode):
    """Mountainash extension relation for non-Substrait operations.

    Handles operations like drop_nulls, with_row_index, explode, etc.
    that are common in DataFrame APIs but not part of Substrait.

    Attributes:
        input: The child relation node
        operation: The extension operation type
        options: Operation-specific configuration
    """

    input: RelationNode
    operation: RKEY_MOUNTAINASH_REL
    options: dict[str, Any] = {}

    @property
    def operation_key(self):
        return self.operation
