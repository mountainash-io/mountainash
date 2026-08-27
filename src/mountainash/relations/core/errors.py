"""Core relations errors (visitor dispatch layer)."""
from __future__ import annotations

from mountainash.core.errors import MountainashError


class UnregisteredRelationNodeError(MountainashError):
    """A relation node type has neither a RelationVisitRegistry handler nor
    an operation_key + RelationOperationRegistry definition (spec §3.5/§3.9)."""

    def __init__(self, node_type: type) -> None:
        self.node_type = node_type
        super().__init__(
            f"{node_type.__name__} cannot be compiled: it has no registered "
            f"visit handler and no operation_key. Either register a handler "
            f"via RelationVisitRegistry.register({node_type.__name__}, handler) "
            f"or define _operation_key plus a RelationOperationDef for it."
        )


class InvalidSampleArgumentsError(MountainashError, ValueError):
    """Relation.sample() argument-contract violation."""


class MaterializationScopeClosedError(MountainashError, RuntimeError):
    """Raised when a closed materialization scope receives new ownership."""
