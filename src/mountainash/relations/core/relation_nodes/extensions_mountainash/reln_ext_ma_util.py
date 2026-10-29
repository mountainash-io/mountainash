"""Extension relation node for mountainash-specific operations.

These operations are not part of the Substrait specification but are
needed for practical DataFrame manipulation.
"""

from __future__ import annotations
import inspect
from typing import Any

from pydantic import model_validator

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

    @model_validator(mode="after")
    def _validate_options(self):
        """Options must match the operation's protocol keyword params
        (spec §3.5). Registry consulted lazily — nodes stay data-only."""
        from mountainash.relations.core.relation_system.relation_mapping.registry import (
            RelationOperationRegistry,
        )

        op = RelationOperationRegistry.get(self.operation)
        sig = op.get_signature()
        if sig is None:
            return self
        kw_params = {
            n: p
            for n, p in sig.parameters.items()
            if p.kind is inspect.Parameter.KEYWORD_ONLY
        }
        unknown = set(self.options) - set(kw_params)
        if unknown:
            raise ValueError(
                f"{self.operation.name}: unknown option(s) {sorted(unknown)}; "
                f"valid options: {sorted(kw_params)}"
            )
        required = {
            n
            for n, p in kw_params.items()
            if p.default is inspect.Parameter.empty
        }
        missing = required - set(self.options)
        if missing:
            raise ValueError(
                f"{self.operation.name}: missing required option(s) {sorted(missing)}"
            )
        return self
