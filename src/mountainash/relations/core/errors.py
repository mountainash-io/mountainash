"""Core relations errors (visitor dispatch layer)."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.conform.structured_transport import StructuredFieldPlanMap

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


class LogicalTerminalRequired(MountainashError, RuntimeError):
    """A native terminal (``collect()``, ``collect_with_drift()``) was
    requested but at least one field's structured plan requires resolving
    through a logical terminal snapshot first (spec Task 5 step 5)."""

    def __init__(self, plans: "StructuredFieldPlanMap") -> None:
        ordered = tuple(plans.values())
        self.fields = tuple(plan.field_name for plan in ordered)
        self.roots = tuple(plan.root.value for plan in ordered)
        self.supported_terminals = (
            "validation", "to_polars", "to_pandas", "to_dict", "to_dicts",
            "to_tuples", "item", "to_dataclasses", "to_pydantic",
        )
        details = ", ".join(
            f"{plan.field_name} ({plan.root.value})" for plan in ordered
        )
        terminals = ", ".join(self.supported_terminals)
        super().__init__(
            f"Logical terminal required for {details}. Use one of: {terminals}"
        )
