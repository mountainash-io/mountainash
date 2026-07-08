"""GroupedRelation for group-by aggregation chains."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ..relation_nodes import AggregateRelNode, RelationNode
from mountainash.relations.core.relation_protocols import GroupedRelationAPIProtocol

if TYPE_CHECKING:
    from .relation import Relation


class GroupedRelation(GroupedRelationAPIProtocol):
    """Intermediate object representing a grouped relation.

    Created by ``Relation.group_by(*keys)`` and consumed by ``.agg()``.
    """

    __slots__ = ("_node", "_keys", "_origin")

    def __init__(
        self, node: RelationNode, keys: list[Any], *, _origin: Any = None
    ) -> None:
        self._node = node
        self._keys = keys
        self._origin = _origin

    def agg(self, *expressions: Any) -> "Relation":
        """Apply aggregate expressions to the grouped relation."""
        node = AggregateRelNode(
            input=self._node,
            keys=self._keys,
            measures=list(expressions),
        )
        # group_by() always supplies _origin, so agg preserves the relation's
        # concrete type (DAGRelation included). No Relation(...) fallback — the
        # invariant test forbids it, and _origin is never None in practice.
        assert self._origin is not None, "GroupedRelation constructed without _origin"
        return self._origin._make(node)
