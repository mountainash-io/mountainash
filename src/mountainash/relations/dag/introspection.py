"""Introspection helpers for RelationDAG."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.relations.dag.dag import RelationDAG
    from mountainash.relations.dag.protocol import RelationDAGProtocol
    from mountainash.core.dtypes.canonical import SchemaTypeStatus


def _name_identity_resolver(dag: RelationDAGProtocol, node: Any) -> Callable[[str], Any]:
    """Validate names-only reference traversal without acquiring dtype evidence."""
    from mountainash.relations.dag.traversal import walk_refs

    for name in walk_refs(node):
        if name not in dag.relations:
            raise KeyError(f"relation {name!r} not in DAG")
        dag.topological_order(target=name)
    def resolve(name: str) -> Any:
        if name not in dag.relations:
            raise KeyError(f"relation {name!r} not in DAG")
        return dag.relations[name]._node

    return resolve


def structural_schema(
    dag: RelationDAGProtocol, name: str
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Infer a named relation's schema without compiling its native plan."""
    if name not in dag.relations:
        raise KeyError(f"relation {name!r} not in DAG")
    # Validate the dependency graph once before recursive structural inspection.
    # Constraint edges are deliberately absent from this traversal.
    dag.topological_order(target=name)
    from mountainash.relations.schema_inference import infer_schema

    def identity_resolver(ref_name: str) -> Any:
        if ref_name not in dag.relations:
            raise KeyError(f"relation {ref_name!r} not in DAG")
        return getattr(dag.relations[ref_name], "_node", None)

    def resolver(ref_name: str) -> dict[str, MountainashDtype | SchemaTypeStatus]:
        node = identity_resolver(ref_name)
        if node is None:
            return {}
        return infer_schema(
            node, ref_resolver=resolver,
            identity_resolver=identity_resolver,
        )

    return resolver(name)


def schema(
    dag: RelationDAGProtocol, name: str
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Return the resolved schema for a registered relation."""
    if name not in dag.relations:
        raise KeyError(f"relation {name!r} not in DAG")
    return dag.ref(name).schema

def _column_count(dag: RelationDAG, name: str) -> int:
    try:
        return len(structural_schema(dag, name))
    except Exception:
        return 0


def describe(dag: RelationDAG) -> dict[str, dict[str, Any]]:
    """Return a structural summary of every registered relation (edges from the graph kernel, columns from schema)."""
    return {
        name: {
            "columns": _column_count(dag, name),
            "dependencies": s["depends_on"],
            "constrained_by": s["constraints"],
        }
        for name, s in dag._graph.describe().items()
    }


def to_dot(dag: RelationDAG) -> str:
    """Return a Graphviz DOT string of the DAG structure (kernel rendering, labelled with column counts)."""
    return dag._graph.to_dot(
        name="RelationDAG",
        graph_attrs=("rankdir=BT",),
        label=lambda name: f"{name} ({_column_count(dag, name)} cols)",
        constraint_attrs=("style=dashed", 'label="FK"'),
    )
