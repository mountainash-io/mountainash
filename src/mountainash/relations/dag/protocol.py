"""Typing protocol for RelationDAG-like graph facades."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from mountainash.conform.drift import ConformCollection
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.core.resource_ref import ResourceRef
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.schema_inference import SchemaTypeStatus
    from mountainash.typespec.spec import ForeignKey


class RelationDAGProtocol(Protocol):
    """Structural protocol for the RelationDAG orchestration + graph-state surface.

    The graph-state attributes (``relations``, ``dependency_edges``,
    ``constraint_edges``, ``constraint_metadata``) are public mutable
    attributes; the supported mutation surface is the method API (``add``,
    ``add_constraint``, ``source``). Direct mutation
    (``dag.relations["x"] = other``) can desynchronise edges from ASTs.

    Thin delegators over the helper modules (``describe``, ``to_dot``,
    ``to_package``, ``validate``, ``validate_quick``) are deliberately
    excluded: the helpers *consume* this protocol, so declaring them here
    would be circular — an alternative DAG implementation gets them for free
    by satisfying the orchestration contract via the same helper functions.
    See ``tests/relations/dag/test_dag_protocol_alignment.py`` for the
    closed-by-default sweep that pins this surface.
    """

    relations: dict[str, Relation]
    assets: dict[str, ResourceRef]
    dependency_edges: set[tuple[str, str]]
    constraint_edges: set[tuple[str, str]]
    constraint_metadata: dict[tuple[str, str], list[ForeignKey]]

    def add(self, name: str, relation: Relation) -> None: ...

    def ref(self, name: str) -> Relation: ...

    def source(self, name: str, data: Any) -> Relation: ...

    def collect(self, name: str, *, backend: str | None = None) -> Any: ...

    def collect_with_drift(
        self, name: str, *, backend: str | None = None
    ) -> ConformCollection: ...

    def execute(self, relation: Relation, *, backend: str | None = None) -> Any: ...

    def topological_order(self, target: str | None = None) -> list[str]: ...

    def schema(self, name: str) -> dict[str, MountainashDtype | SchemaTypeStatus]: ...

    def add_constraint(self, child: str, fk: ForeignKey) -> None: ...

    def constraints_for(self, child: str) -> list[ForeignKey]: ...
