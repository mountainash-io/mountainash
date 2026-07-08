"""DAGRelation — a type-preserving Relation bound to a RelationDAG.

`dag.ref()`/`dag.source()` return this. Chaining preserves the type (via
`_make`); terminals compile through `dag.execute()` without registering or
mutating the DAG. Its delta over Relation is confined to three behaviours:
terminal ownership, type-preserving chaining, and DAG-ownership propagation
through combining builders (added in Task 5). The AST, visitor, and
compilation flow are untouched — a DAGRelation's tree is indistinguishable
from any other.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.relations.core.relation_api.relation import Relation

if TYPE_CHECKING:
    from mountainash.relations.core.relation_nodes import RelationNode
    from mountainash.relations.dag.protocol import RelationDAGProtocol


class DAGRelation(Relation):
    """A Relation created from a RelationDAG that owns DAG-aware terminals.

    No __slots__: Relation carries a __dict__ (only RelationBase declares
    __slots__), so `self._dag` lives there. Adding __slots__ here saves
    nothing and risks slot-layout confusion.
    """

    def __init__(self, node: "RelationNode", dag: "RelationDAGProtocol") -> None:
        super().__init__(node)
        self._dag = dag

    def _make(self, node: "RelationNode") -> "DAGRelation":
        return DAGRelation(node, self._dag)

    def _compile_and_execute(self) -> Any:
        result, _visitor = self._dag._execute_with_visitor(self)
        return result

    def _compile_and_execute_with_visitor(
        self, backend: "str | None" = None
    ) -> "tuple[Any, Any]":
        return self._dag._execute_with_visitor(self, backend=backend)
