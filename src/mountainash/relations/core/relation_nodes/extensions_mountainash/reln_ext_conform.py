"""Conform relation node — defers schema conformance to compile time.

At build time, Relation.conform(spec) wraps the current plan in this node.
At compile time, the visitor applies the full TypeSpec transform pipeline
(missingValues, type casting, fieldsMatch enforcement) via apply_conform(),
which has access to the native backend object and its column schema.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import ConfigDict

from ..reln_base import RelationNode


class ConformRelNode(RelationNode):
    """Apply schema conformance to a child relation.

    Stores the TypeSpec as part of the plan tree. The actual transformation
    is applied by the visitor at compile time when column information is
    available.

    Attributes:
        input: The child relation to conform.
        spec: A TypeSpec (or Frictionless dict) describing the target schema.
        contract: Optional raw reconciliation-contract override captured from
            ``Relation.conform(spec, contract=...)``. A scalar string applies
            to the extension dimensions (``data_type``, ``keys``) only; a
            dict maps dimension -> mode explicitly. Resolved against
            ``TypeSpec.contract`` and the ``fields_match`` preset at compile
            time via ``resolve_contract`` (see item 48 PR-B).
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    input: RelationNode
    spec: Any
    contract: Optional[Any] = None

    def accept(self, visitor: Any) -> Any:
        return visitor.visit(self)
