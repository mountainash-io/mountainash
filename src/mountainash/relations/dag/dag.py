"""RelationDAG — orchestrator over named Relations.

This is a thin container around the existing relations AST + visitor — not
a new visitor stack. The DAG walks each named relation's tree once at add()
time to derive dependency edges (from RefRelNode instances), then defers
materialization to ``collect()`` (added in Task 17).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from mountainash.core.constants import CONST_BACKEND
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

    # ------------------------------------------------------------------
    # Task 17: collect() — topological compilation with per-call cache
    # ------------------------------------------------------------------

    def collect(self, name: str, *, backend: Optional[str] = None) -> Any:
        """Topologically walk dependencies of ``name`` and compile each in order.

        Each upstream relation's compiled value is cached for the duration of
        this call and exposed to the visitor as ``ref_resolver(name)``.
        Returns the backend-native compiled value for ``name`` itself.
        """
        if name not in self.relations:
            raise KeyError(f"relation {name!r} not in DAG")

        from mountainash.relations.core.relation_protocols.relsys_base import (
            get_relation_system,
        )
        from mountainash.expressions.core.expression_system.expsys_base import (
            get_expression_system,
        )
        from mountainash.expressions.core.unified_visitor import (
            UnifiedExpressionVisitor,
        )
        from mountainash.relations.core.unified_visitor.relation_visitor import (
            UnifiedRelationVisitor,
        )

        resolved_backend = self._resolve_backend_const(backend, name)
        relation_system_cls = get_relation_system(resolved_backend)
        relation_system = relation_system_cls()
        expression_system_cls = get_expression_system(resolved_backend)
        expression_system = expression_system_cls()
        expr_visitor = UnifiedExpressionVisitor(expression_system)

        cache: dict[str, Any] = {}

        def resolver(n: str) -> Any:
            return cache[n]

        visitor = UnifiedRelationVisitor(
            relation_system,
            expression_visitor=expr_visitor,
            ref_resolver=resolver,
        )

        order = self.topological_order(target=name)
        for n in order:
            rel = self.relations[n]
            root = getattr(rel, "_node", None)
            if root is None:
                raise ValueError(f"relation {n!r} has no _node attribute")
            cache[n] = root.accept(visitor)
        return cache[name]

    def to_package(self) -> Any:
        """Export this DAG as a Frictionless DataPackage descriptor.

        Each named relation must either:
        1. Have a ResourceReadRelNode at its root (so we can reuse the original
           DataResource), OR
        2. Expose an output schema we can derive (currently only the first case
           is supported — derived synthesis is deferred).

        Raises ``MissingResourceSchema`` if any relation has neither.
        Assets pass through to the returned package unchanged.
        """
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ResourceReadRelNode,
        )
        from mountainash.typespec.datapackage import DataPackage, DataResource
        from .errors import MissingResourceSchema

        resources: list[DataResource] = []
        missing: list[str] = []

        for name, relation in self.relations.items():
            root = getattr(relation, "_node", None)
            if isinstance(root, ResourceReadRelNode):
                res = root.resource
                if res.name != name:
                    res = res.model_copy(update={"name": name})
                resources.append(res)
                continue
            # No source resource — try the relation's declared output schema
            output_schema = getattr(relation, "output_schema", None)
            if output_schema is None:
                missing.append(name)
                continue
            resources.append(
                DataResource(  # type: ignore[call-arg]
                    name=name,
                    path=f"{name}.csv",  # placeholder
                    type="table",
                    format="csv",
                    table_schema=output_schema,
                )
            )

        # Asset resources pass through
        for name, ref in self.assets.items():
            res = ref.resource
            if res.name != name:
                res = res.model_copy(update={"name": name})
            resources.append(res)

        if missing:
            raise MissingResourceSchema(
                f"cannot export to DataPackage; relations without schema: {missing}"
            )
        return DataPackage(resources=resources)

    def _resolve_backend_const(
        self, backend: Optional[str], target_name: str
    ) -> CONST_BACKEND:
        """Determine the CONST_BACKEND to use for compilation.

        If ``backend`` is given explicitly, honour it. Otherwise walk the
        dependency tree of ``target_name`` to find the first ReadRelNode and
        detect its backend. Falls back to Polars when no ReadRelNode is found
        (e.g. pure SourceRelNode / inline data trees).
        """
        if backend is not None:
            try:
                return CONST_BACKEND(backend.lower())
            except ValueError:
                raise ValueError(f"unknown backend: {backend!r}")

        # Walk through relations in topological order and look for a
        # ReadRelNode to detect the backend from its dataframe.
        from mountainash.relations.core.relation_api.relation_base import (
            RelationBase,
        )
        from mountainash.expressions.core.expression_system.expsys_base import (
            identify_backend,
        )
        from mountainash.relations.dag.errors import RelationDAGRequired

        order = self.topological_order(target=target_name)
        for n in order:
            rel = self.relations[n]
            root = getattr(rel, "_node", None)
            if root is None:
                continue
            try:
                read_node = RelationBase._find_leaf_read_node(root)
            except (ValueError, AttributeError, RelationDAGRequired):
                # Node type not handled (e.g. RefRelNode) — skip, try next.
                continue
            if read_node is not None:
                try:
                    return identify_backend(read_node.dataframe)
                except Exception:
                    pass
        # No ReadRelNode found — default to Polars (SourceRelNode / inline data).
        return CONST_BACKEND.POLARS
