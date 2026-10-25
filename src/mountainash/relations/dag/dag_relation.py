"""DAGRelation — a type-preserving Relation bound to a RelationDAG.

`dag.ref()`/`dag.source()` return this. Chaining preserves the type (via
`_make`); terminals compile through `dag.execute()` without registering or
mutating the DAG. Its behavior adds terminal ownership, type-preserving
chaining, DAG-ownership propagation through combining builders, and structural
reference resolution for ``assess_drift``. Ordinary schema resolution is
inherited from ``Relation`` and uses the owning DAG resolver.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.execution.preparation import ExecutionPhase

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
        from mountainash.core.capabilities.policy import _resolve_policy

        result, _visitor = self._dag._execute_with_visitor(
            self, execution_policy=_resolve_policy(),
        )
        return result

    def _compile_and_execute_with_visitor(
        self,
        backend: "str | None" = None,
        execution_context: Any = None,
        *, phase: ExecutionPhase = ExecutionPhase.EXECUTE, retain_execution_scope: bool = False,
    ) -> "tuple[Any, Any]":
        from mountainash.core.capabilities.policy import _resolve_policy

        execution_policy = (
            execution_context.policy if execution_context is not None else _resolve_policy()
        )
        return self._dag._execute_with_visitor(
            self, backend=backend, execution_policy=execution_policy,
            phase=phase, execution_context=execution_context,
            retain_execution_scope=retain_execution_scope,
        )

    def explain(self) -> str:
        """Describe the expanded DAG recipe without compiling named values."""
        result, _visitor = self._compile_and_execute_with_visitor(
            phase=ExecutionPhase.EXPLAIN,
        )
        return result


    def assess_drift(self) -> "list":
        """Assess drift structurally, without compiling the relation."""
        from mountainash.relations.dag.introspection import _name_identity_resolver, structural_schema
        from mountainash.relations.schema_inference import (
            assess_drift as _assess_drift,
        )

        identity_resolver = _name_identity_resolver(self._dag, self._node)

        def resolver(ref_name: str):
            return structural_schema(self._dag, ref_name)

        return _assess_drift(
            self._node, ref_resolver=resolver,
            identity_resolver=identity_resolver,
        )


def _dag_of(rel: Any) -> "RelationDAGProtocol | None":
    """The DAG a relation is bound to, or None for a plain Relation / raw data."""
    return getattr(rel, "_dag", None)


def _resolve_shared_dag(operands: "list[Any]") -> "RelationDAGProtocol | None":
    """Validate that all DAG-bound operands share one DAG; return it (or None if
    none is DAG-bound). Raise ValueError on a cross-DAG mix. Operands that are
    not relations (raw data) contribute no DAG."""
    dags = [d for d in (_dag_of(r) for r in operands) if d is not None]
    if not dags:
        return None
    first = dags[0]
    for d in dags[1:]:
        if d is not first:
            raise ValueError(
                "cannot combine relations bound to different DAG instances"
            )
    return first
