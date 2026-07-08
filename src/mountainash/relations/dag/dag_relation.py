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

    @property
    def schema(self) -> dict:
        """Output schema, resolving ``RefRelNode`` leaves via the bound DAG.

        Mirrors ``dag.schema(name)``'s resolver so the schema-family
        properties (``columns``/``dtypes``/``width``/``output_schema``, which
        derive from this) return real schemas over ref-bearing trees instead
        of the degenerate ``{}`` a plain Relation infers.
        """
        from mountainash.relations.schema_inference import infer_schema

        def resolver(ref_name: str):
            return self._dag.schema(ref_name)

        return infer_schema(self._node, ref_resolver=resolver)

    def assess_drift(self) -> "list":
        """Schema-only drift pre-flight, resolving ``RefRelNode`` leaves via the
        bound DAG. The base method compiles nothing, so the choke-point
        overrides do not cover it — it needs its own resolver."""
        from mountainash.relations.schema_inference import (
            assess_drift as _assess_drift,
        )

        def resolver(ref_name: str):
            return self._dag.schema(ref_name)

        return _assess_drift(self._node, ref_resolver=resolver)
