"""Typing protocol for RelationDAG-like graph facades."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from mountainash.core.resource_ref import ResourceRef


class RelationDAGProtocol(Protocol):
    """Structural protocol for helpers that operate on a RelationDAG facade."""

    relations: dict[str, Any]
    assets: dict[str, ResourceRef]
    dependency_edges: set[tuple[str, str]]
    constraint_edges: set[tuple[str, str]]

    def add(self, name: str, relation: Any) -> None: ...

    def ref(self, name: str) -> Any: ...

    def collect(self, name: str, *, backend: str | None = None) -> Any: ...
