"""GroupedRelation for group-by aggregation chains."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ..relation_nodes import AggregateRelNode, RelationNode

if TYPE_CHECKING:
    from .relation import Relation


class GroupedRelation:
    """Intermediate object representing a grouped relation.

    Created by ``Relation.group_by(*keys)`` and consumed by ``.agg()``.
    """

    __slots__ = ("_node", "_keys")

    def __init__(self, node: RelationNode, keys: list[Any]) -> None:
        self._node = node
        self._keys = keys

    def agg(self, *expressions: Any) -> "Relation":
        """Apply aggregate expressions to the grouped relation."""
        from .relation import Relation

        return Relation(
            AggregateRelNode(
                input=self._node,
                keys=self._keys,
                measures=list(expressions),
            )
        )
