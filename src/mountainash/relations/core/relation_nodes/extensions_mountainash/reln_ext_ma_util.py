"""Extension relation node for mountainash-specific operations.

These operations are not part of the Substrait specification but are
needed for practical DataFrame manipulation.
"""

from __future__ import annotations
from typing import Any

from mountainash.core.constants import ExtensionRelOperation

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
    operation: ExtensionRelOperation
    options: dict[str, Any] = {}

    def accept(self, visitor: Any) -> Any:
        """Accept a visitor for double-dispatch."""
        return visitor.visit_extension_rel(self)
