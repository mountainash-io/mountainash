"""Introspection helpers for RelationDAG."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.relations.dag.protocol import RelationDAGProtocol
    from mountainash.relations.schema_inference import SchemaTypeStatus


def schema(
    dag: RelationDAGProtocol, name: str
) -> dict[str, MountainashDtype | SchemaTypeStatus]:
    """Return the inferred output schema for a named relation.

    Values are canonical ``MountainashDtype`` where inferable, or a
    ``SchemaTypeStatus`` (UNKNOWN / UNCONSTRAINED) where not.
    """
    if name not in dag.relations:
        raise KeyError(f"relation {name!r} not in DAG")
    node = getattr(dag.relations[name], "_node", None)
    if node is None:
        return {}

    from mountainash.relations.schema_inference import infer_schema

    def resolver(
        ref_name: str,
    ) -> dict[str, MountainashDtype | SchemaTypeStatus]:
        return schema(dag, ref_name)

    return infer_schema(node, ref_resolver=resolver)


def describe(dag: RelationDAGProtocol) -> dict[str, dict[str, Any]]:
    """Return a structural summary of every registered relation."""
    result: dict[str, dict[str, Any]] = {}
    for name in dag.relations:
        deps = sorted(u for u, d in dag.dependency_edges if d == name)
        constrained = sorted(u for u, d in dag.constraint_edges if d == name)
        try:
            col_count = len(schema(dag, name))
        except Exception:
            col_count = 0
        result[name] = {
            "columns": col_count,
            "dependencies": deps,
            "constrained_by": constrained,
        }
    return result


def to_dot(dag: RelationDAGProtocol) -> str:
    """Return a Graphviz DOT string of the DAG structure."""
    lines = ["digraph RelationDAG {", "    rankdir=BT;"]

    for name in sorted(dag.relations):
        try:
            col_count = len(schema(dag, name))
        except Exception:
            col_count = 0
        lines.append(f'    "{name}" [label="{name} ({col_count} cols)"];')

    for u, d in sorted(dag.dependency_edges):
        lines.append(f'    "{u}" -> "{d}";')

    for u, d in sorted(dag.constraint_edges):
        lines.append(f'    "{u}" -> "{d}" [style=dashed, label="FK"];')

    lines.append("}")
    return "\n".join(lines)
