"""``Graph[N]`` — the node/edge container shared by ``RelationDAG`` and ``Pipeline``.

Two edge sets, kept sharply separate (two-edge-graph-model): ``dependency_edges``
drive ordering; ``constraint_edges`` are metadata and never affect execution.
The kernel holds no execution, caching, persistence or AST traversal — owners
pass it derived dependency names.
"""
from __future__ import annotations

from typing import Any, Generic, Iterable, TypeVar

from mountainash.graph.algorithms import ancestors as _ancestors
from mountainash.graph.algorithms import parallel_layers as _layers
from mountainash.graph.algorithms import topological_order as _topo
from mountainash.graph.errors import CycleError, DuplicateNodeError, UnknownNodeError

N = TypeVar("N")


class Graph(Generic[N]):
    def __init__(self) -> None:
        self.nodes: dict[str, N] = {}
        self.dependency_edges: set[tuple[str, str]] = set()
        self.constraint_edges: set[tuple[str, str]] = set()
        self.constraint_metadata: dict[tuple[str, str], list[Any]] = {}

    def add(self, name: str, node: N, *, depends_on: Iterable[str] = ()) -> None:
        if name in self.nodes:
            raise DuplicateNodeError(f"node {name!r} already in graph")
        self.nodes[name] = node
        for upstream in depends_on:
            self.dependency_edges.add((upstream, name))

    def add_constraint(self, parent: str, child: str, meta: Any = None) -> None:
        edge = (parent, child)
        self.constraint_edges.add(edge)
        if meta is not None:
            bucket = self.constraint_metadata.setdefault(edge, [])
            if meta not in bucket:
                bucket.append(meta)

    def topological_order(self, target: str | None = None) -> list[str]:
        if target is not None and target not in self.nodes:
            raise UnknownNodeError(target)
        try:
            return _topo(set(self.nodes), self.dependency_edges, target)
        except ValueError as e:
            raise CycleError(str(e)) from e

    def ancestors(self, name: str) -> set[str]:
        return _ancestors(self.dependency_edges, name)

    def descendants(self, name: str) -> set[str]:
        out: set[str] = set()
        frontier = {name}
        while frontier:
            nxt = {d for (u, d) in self.dependency_edges if u in frontier} - out
            out |= nxt
            frontier = nxt
        return out

    def parallel_layers(self, order: list[str]) -> list[list[str]]:
        return _layers(self.dependency_edges, order)

    def describe(self) -> dict[str, dict]:
        return {
            n: {
                "depends_on": sorted(u for (u, d) in self.dependency_edges if d == n),
                "constraints": sorted(p for (p, c) in self.constraint_edges if c == n),
            }
            for n in self.nodes
        }

    def to_dot(self) -> str:
        lines = ["digraph G {"]
        lines += [f'  "{n}";' for n in self.nodes]
        lines += [f'  "{u}" -> "{d}";' for (u, d) in sorted(self.dependency_edges)]
        lines += [f'  "{p}" -> "{c}" [style=dashed];' for (p, c) in sorted(self.constraint_edges)]
        lines.append("}")
        return "\n".join(lines)
