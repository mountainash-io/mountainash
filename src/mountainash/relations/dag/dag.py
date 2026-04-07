"""RelationDAG — orchestrator over named Relations.

This is a thin container around the existing relations AST + visitor — not
a new visitor stack. The DAG walks each named relation's tree once at add()
time to derive dependency edges (from RefRelNode instances), then defers
materialization to ``collect()`` (added in Task 17).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    RefRelNode,
)
from .resource_ref import ResourceRef


def _walk_refs(node: Any) -> set[str]:
    """Recursively collect names of all RefRelNode descendants under ``node``."""
    found: set[str] = set()
    if node is None:
        return found
    if isinstance(node, RefRelNode):
        found.add(node.name)
    # Walk children using known attribute names from relation node subtypes:
    # - input: FilterRelNode, SortRelNode, ProjectRelNode, FetchRelNode, AggregateRelNode
    # - left / right: JoinRelNode
    # - inputs: SetRelNode (list)
    for attr in ("input", "left", "right", "inputs"):
        child = getattr(node, attr, None)
        if child is None:
            continue
        if isinstance(child, list):
            for c in child:
                found |= _walk_refs(c)
        else:
            found |= _walk_refs(child)
    return found


class RelationDAG:
    """Container for named Relations with dependency and constraint edge sets."""

    def __init__(self) -> None:
        self.relations: dict[str, Any] = {}
        self.assets: dict[str, ResourceRef] = {}
        self.dependency_edges: set[tuple[str, str]] = set()
        self.constraint_edges: set[tuple[str, str]] = set()

    def add(self, name: str, relation: Any) -> None:
        """Add a named relation to the DAG.

        Automatically walks the relation tree for ``RefRelNode`` instances and
        records dependency edges from the referenced name to ``name``.

        Raises ``ValueError`` if ``name`` is already in the DAG.
        """
        if name in self.relations:
            raise ValueError(f"relation {name!r} already in DAG")
        self.relations[name] = relation
        root = getattr(relation, "_node", None)
        for upstream in _walk_refs(root):
            self.dependency_edges.add((upstream, name))

    def ref(self, name: str) -> Any:
        """Return a Relation backed by a ``RefRelNode`` for ``name``.

        Chaining ``.filter()``, ``.select()``, etc. on the returned object
        builds a normal relational AST with the ref at its leaf. The dependency
        edge is recorded when ``add()`` is later called with the result.
        """
        from mountainash.relations.core.relation_api.relation import Relation
        node = RefRelNode(name=name)
        return Relation(node)

    def topological_order(self, target: Optional[str] = None) -> list[str]:
        """Return a topologically sorted list of relation names.

        If ``target`` is given, only ancestors of ``target`` (and ``target``
        itself) are included.

        Raises ``ValueError`` if a cycle is detected.
        """
        nodes: set[str] = set(self.relations.keys())
        if target is not None:
            # Restrict to ancestors of target (including target itself)
            wanted: set[str] = {target}
            stack = [target]
            while stack:
                cur = stack.pop()
                for u, d in self.dependency_edges:
                    if d == cur and u not in wanted:
                        wanted.add(u)
                        stack.append(u)
            nodes = wanted

        # Kahn's algorithm
        indeg: dict[str, int] = {n: 0 for n in nodes}
        adj: dict[str, list[str]] = defaultdict(list)
        for u, d in self.dependency_edges:
            if u in nodes and d in nodes:
                adj[u].append(d)
                indeg[d] += 1
        ready = sorted(n for n, i in indeg.items() if i == 0)
        out: list[str] = []
        while ready:
            n = ready.pop(0)
            out.append(n)
            for m in sorted(adj[n]):
                indeg[m] -= 1
                if indeg[m] == 0:
                    ready.append(m)
        if len(out) != len(nodes):
            raise ValueError(
                f"cycle detected in dependency_edges (target={target!r})"
            )
        return out
