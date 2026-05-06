"""Base class for relation API builder namespaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash.relations.core.relation_nodes.reln_base import RelationNode


class BaseRelationAPIBuilder:
    """Base class for all relation API builder namespaces.

    Provides shared utilities for node access and building new Relation
    instances. Subclasses implement domain-specific operations.
    """

    __slots__ = ("_relation",)

    def __init__(self, relation: Any) -> None:
        self._relation = relation

    @property
    def _node(self) -> RelationNode:
        return self._relation._node

    def _build(self, node: RelationNode) -> Any:
        from ..relation import Relation
        return Relation(node)
