
from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
from mountainash.relations.dag.traversal import walk_refs as _walk_refs


def _consumer_prototype(family: CONST_BACKEND, dialect: str | None) -> Any:
    """Alias for :func:`_anchor_prototype` (the consumer-side prototype
    ``_coerce_to_match`` needs as its target object). Same function, renamed
    at the call site so item 97's resolver-time coercion reads naturally
    without rewriting item 92's territory."""
    return _anchor_prototype(family, dialect)


def _anchor_prototype(family: CONST_BACKEND, dialect: str | None) -> Any:
    """A lightweight empty object of *family* for coercion to target."""
    if family is CONST_BACKEND.POLARS:
        import polars as pl
        return pl.DataFrame({}).lazy()
    if family is CONST_BACKEND.IBIS:
        import ibis
        return ibis.memtable({})
    if family is CONST_BACKEND.NARWHALS:
        import narwhals as nw
        if dialect == "narwhals-polars":
            import polars as pl
            return nw.from_native(pl.DataFrame({}), eager_only=True)
        if dialect == "narwhals-pyarrow":
            import pyarrow as pa
            return nw.from_native(pa.table({}), eager_only=True)
        import pandas as pd
        return nw.from_native(pd.DataFrame({}), eager_only=True)
    return None


def _is_lazy_narwhals(obj: Any) -> bool:
    """True iff *obj* is a narwhals LazyFrame."""
    try:
        import narwhals as nw
        return isinstance(obj, nw.LazyFrame)
    except Exception:
        return False

if TYPE_CHECKING:
    from mountainash.conform.drift import ConformCollection
    from mountainash.core.dtypes import MountainashDtype
    from mountainash.core.resource_ref import ResourceRef
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.dag.dag_relation import DAGRelation
    from mountainash.relations.dag.errors import UnknownRelationRef
    from mountainash.relations.schema_inference import SchemaTypeStatus
    from mountainash.typespec.spec import ForeignKey
    from .validation import DAGValidationResult

"""RelationDAG — orchestrator over named Relations.

This is a thin container around the existing relations AST + visitor — not
a new visitor stack. The DAG walks each named relation's tree once at add()
time to derive dependency edges (from RefRelNode instances), then defers
materialization to ``collect()`` (added in Task 17).
"""

class RelationDAG:
    """Container for named Relations with dependency and constraint edge sets.

    ``relations``, ``dependency_edges``, ``constraint_edges`` and
    ``constraint_metadata`` are public mutable attributes; the supported
    mutation surface is the method API (``add``, ``add_constraint``,
    ``source``). Direct mutation (``dag.relations["x"] = other``) can
    desynchronise edges from ASTs.
    """

    def __init__(self) -> None:
        self.relations: dict[str, Relation] = {}
        self.assets: dict[str, ResourceRef] = {}
        self.dependency_edges: set[tuple[str, str]] = set()
        self.constraint_edges: set[tuple[str, str]] = set()
        # Structured FK detail, strictly subordinate to constraint_edges:
        # set(constraint_metadata.keys()) ⊆ constraint_edges always. An edge
        # with no metadata entry is a topology-only relationship (consumers
        # needing field-level detail MUST read constraint_metadata; absent
        # means non-actionable, not "fields = empty"). Sole supported
        # writers: add_constraint() and DataPackage.to_relation_dag().
        self.constraint_metadata: dict[tuple[str, str], list["ForeignKey"]] = {}

    def add(self, name: str, relation: Relation) -> None:
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

    def ref(self, name: str) -> "DAGRelation":
        """Return a DAGRelation backed by a ``RefRelNode`` for ``name``.

        Chaining ``.filter()``, ``.select()``, etc. preserves the DAGRelation
        type and its DAG binding; terminals compile through this DAG. The
        dependency edge is recorded only when ``add()`` is later called.
        """
        from mountainash.relations.dag.dag_relation import DAGRelation

        node = RefRelNode(name=name)
        return DAGRelation(node, self)

    def source(self, name: str, data: Any) -> "DAGRelation":
        """Register source data and return a DAGRelation ref for downstream use."""
        from mountainash.relations.core.relation_api.relation import relation

        self.add(name, relation(data))
        return self.ref(name)

    def add_constraint(self, child: str, fk: "ForeignKey") -> None:
        """Declare a foreign-key constraint on a *derived* relation.

        Populates ``constraint_edges`` and ``constraint_metadata`` together
        under the same ``(target, child)`` key. Never touches
        ``dependency_edges`` (two-edge-graph-model). This is the sole
        supported mutation path for ``constraint_metadata`` — do not mutate
        the dict directly.

        Raises:
            KeyError: ``child`` is not a relation in this DAG.
            ValueError: the FK target is not a relation in this DAG, or
                ``child`` is a pass-through resource — its foreign keys
                belong in the resource's ``table_schema``
                (lossless-frictionless-storage), not here.
        """
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ResourceReadRelNode,
        )

        if child not in self.relations:
            raise KeyError(f"unknown relation {child!r}")
        root = getattr(self.relations[child], "_node", None)
        if isinstance(root, ResourceReadRelNode):
            raise ValueError(
                f"{child!r} is a pass-through resource; declare its foreign "
                "keys in the resource's table_schema, not via add_constraint()."
            )
        # Empty/self reference normalises to the (child, child) edge key —
        # the same rule as the DataPackage parse path.
        ref_resource = fk.reference.resource
        target = ref_resource if ref_resource else child
        if target != child and target not in self.relations:
            raise ValueError(f"unknown foreign-key target {target!r}")
        edge = (target, child)
        self.constraint_edges.add(edge)
        bucket = self.constraint_metadata.setdefault(edge, [])
        if fk not in bucket:  # equality dedup; ForeignKey is unhashable
            bucket.append(fk)

    def constraints_for(self, child: str) -> "list[ForeignKey]":
        """All declared foreign keys whose child side is ``child``.

        Derived from ``constraint_metadata`` (FKs in insertion order per
        edge; edges in insertion order). Topology-only constraint edges
        (no metadata entry) contribute nothing.
        """
        out: "list[ForeignKey]" = []
        for (_target, c), fks in self.constraint_metadata.items():
            if c == child:
                out.extend(fks)
        return out

    def topological_order(self, target: Optional[str] = None) -> list[str]:
        """Return a topologically sorted list of relation names.

        If ``target`` is given, only ancestors of ``target`` (and ``target``
        itself) are included.

        Delegates to the shared :func:`mountainash.graph.topological_order`
        (Kahn's algorithm with ancestor filtering); the DAG only supplies its
        node set and ``dependency_edges`` as the graph's edge set.

        Raises ``ValueError`` if a cycle is detected.
        """
        from mountainash.graph import topological_order as _topological_order

        return _topological_order(
            set(self.relations.keys()), self.dependency_edges, target
        )

    # ------------------------------------------------------------------
    # Task 17: collect() — topological compilation with per-call cache
    # ------------------------------------------------------------------

    def collect(self, name: str, *, backend: Optional[str] = None) -> Any:
        """Topologically walk dependencies and materialize residue once."""
        result, visitor = self._collect_with_visitor(name, backend=backend)
        has_trace = any(
            trace.records for trace in visitor.diagnostic_traces.values()
        )
        if not visitor.residue_checks and not has_trace:
            return result

        from mountainash.core.limitations import enrich_materialization
        from mountainash.core.types import (
            is_ibis_table,
            is_narwhals_lazyframe,
            is_polars_lazyframe,
        )
        from mountainash.relations.core.relation_api.relation import _materialize

        original = result
        result = enrich_materialization(
            visitor.backend,
            lambda: _materialize(result, unwrap=False),
            diagnostic_trace=visitor._active_diagnostic_trace(),
            residue_checks=visitor.residue_checks,
        )
        if is_ibis_table(original) and not is_ibis_table(result):
            import ibis
            result = ibis.memtable(result)
        if is_polars_lazyframe(original) or is_narwhals_lazyframe(original):
            result = result.lazy()
        return result

    def collect_with_drift(
        self, name: str, *, backend: Optional[str] = None
    ) -> "ConformCollection":
        """Collect ``name`` and return the frame plus per-conform-node drift reports.

        DAG-level counterpart to :meth:`Relation.collect_with_drift`. A
        ``freeze`` policy (on any dimension, including ``keys``) still
        raises ``SchemaDriftError`` before this returns — the exception's
        ``.drift`` carries the tripping node's report.

        Returns:
            A :class:`~mountainash.conform.drift.ConformCollection` with the
            materialized ``frame``, the ordered list of ``drifts`` collected
            during compilation (one per conform node that assessed
            anything), and ``effective_schema`` derived from the ACTUAL
            output frame.
        """
        from mountainash.conform.drift import ConformCollection
        from mountainash.relations.core.relation_api.relation import _materialize
        from mountainash.relations.schema_inference import _schema_from_dataframe
        from mountainash.core.limitations import enrich_materialization

        result, visitor = self._collect_with_visitor(name, backend=backend)
        frame = enrich_materialization(
            visitor.backend,
            lambda: _materialize(result),
            diagnostic_trace=visitor._active_diagnostic_trace(),
            residue_checks=visitor.residue_checks,
        )
        return ConformCollection(
            frame=frame,
            drifts=list(visitor.drift_reports),
            effective_schema=_schema_from_dataframe(frame),
        )

    def _collect_with_visitor(
        self, name: str, *, backend: Optional[str] = None
    ) -> "tuple[Any, Any]":
        """Shared core for :meth:`collect` / :meth:`collect_with_drift`."""
        if name not in self.relations:
            raise KeyError(f"relation {name!r} not in DAG")

        rel = self.relations[name]
        root = getattr(rel, "_node", None)
        if root is None:
            raise ValueError(f"relation {name!r} has no _node attribute")

        # All refs reachable via dependency_edges for this name
        order = self.topological_order(target=name)
        ref_names = {n for n in order if n != name}

        return self._compile_with_refs(
            root,
            ref_names,
            backend=backend,
            backend_target_name=name,
            key_target_name=name,
        )

    def execute(self, relation: Relation, *, backend: Optional[str] = None) -> Any:
        """Compile an ad-hoc relation against this DAG without registering it.

        Any ``RefRelNode`` leaves in the relation's AST are resolved from
        ``self.relations`` (transitively), but the relation itself is never
        added to the DAG — no mutations to ``self.relations`` or
        ``self.dependency_edges``.

        Raises ``ValueError`` if the relation has no ``_node`` attribute.
        Raises ``KeyError`` if a referenced name is not in the DAG.
        """
        result, _visitor = self._execute_with_visitor(relation, backend=backend)
        return result

    def _execute_with_visitor(
        self, relation: "Relation", *, backend: Optional[str] = None
    ) -> "tuple[Any, Any]":
        """``execute()`` variant returning ``(result, visitor)`` for terminals
        needing post-compile visitor state (e.g. ``collect_with_drift``).

        Ad-hoc: resolves ref leaves transitively, never mutates the DAG, and
        never assigns the target a key identity (``key_target_name=None``).
        """
        node = getattr(relation, "_node", None)
        if node is None:
            raise ValueError("relation has no _node attribute")

        # Collect all transitive ref names
        all_refs: set[str] = set()
        pending = _walk_refs(node)
        while pending:
            name = pending.pop()
            if name not in self.relations:
                raise self._unknown_ref_error(name)
            if name not in all_refs:
                all_refs.add(name)
                # Walk the registered relation's node for further refs
                ref_node = getattr(self.relations[name], "_node", None)
                if ref_node is not None:
                    pending |= _walk_refs(ref_node) - all_refs

        # Pick a backend target name for detection (first ref alphabetically).
        # If no refs and no explicit backend, _compile_with_refs's own
        # ad-hoc-node fallback branch (via _resolve_actual_identity_for_node)
        # detects family+dialect together from this same node's own leaf --
        # this used to duplicate that detection here (family only, no
        # dialect) before immediately re-detecting it inside
        # _compile_with_refs. Removed as dead weight (round-2: "the
        # resolver still double-walks").
        target_name = sorted(all_refs)[0] if all_refs else None

        return self._compile_with_refs(
            node,
            all_refs,
            backend=backend,
            backend_target_name=target_name,
            key_target_name=None,
        )

    def _compile_with_refs(
        self,
        node: Any,
        ref_names: set[str],
        *,
        backend: Optional[str] = None,
        backend_target_name: Optional[str] = None,
        key_target_name: Optional[str] = None,
    ) -> "tuple[Any, Any]":
        """Compile ``node`` after materialising all relations in ``ref_names``.

        This is the shared compilation core used by both ``collect()`` and
        ``execute()``.  It builds a visitor with a ``ref_resolver`` closure
        over a per-call cache, compiles every relation named in ``ref_names``
        in topological order, then compiles ``node`` itself and returns
        ``(result, visitor)`` — callers needing post-compile visitor state
        (e.g. ``collect_with_drift()``'s ``visitor.drift_reports``) can
        retrieve it without a second compilation pass.
        """
        missing_refs = sorted(n for n in ref_names if n not in self.relations)
        if missing_refs:
            raise self._unknown_ref_error(missing_refs[0])
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

        # Resolve the anchor's PHYSICAL identity (family, dialect) once, via
        # the combined resolver -- walking the named anchor relation (or,
        # for an ad-hoc execute() node with no refs and no target name, the
        # node's own leaf) -- THEN apply any explicit backend= override on
        # top, coherently. Round-2 fix: the branches previously combined an
        # override-derived family with a dialect string detected
        # independently from a leaf whose actual family might not match the
        # override, constructing an invalid (family, dialect) hybrid (e.g.
        # PolarsRelationSystem(dialect="narwhals-pandas")) whenever backend=
        # was given but disagreed with the anchor's own physical family.
        # The dialect is now trusted ONLY when it was actually detected on
        # a leaf belonging to the resolved (possibly overridden) family.
        if backend_target_name is not None:
            actual_family, actual_dialect = self._resolve_actual_identity_for(
                backend_target_name
            )
        elif ref_names:
            # Use the first ref (alphabetically, for determinism) for detection
            anchor_name = sorted(ref_names)[0]
            actual_family, actual_dialect = self._resolve_actual_identity_for(
                anchor_name
            )
        else:
            # No refs and no target name -- ad-hoc node with no registered
            # name; probe its own leaf directly.
            actual_family, actual_dialect = self._resolve_actual_identity_for_node(
                node
            )

        if backend is not None:
            try:
                resolved_backend = CONST_BACKEND(backend.lower())
            except ValueError:
                raise ValueError(f"unknown backend: {backend!r}")
            # Only trust the detected dialect if it actually belongs to the
            # resolved (possibly overridden) family -- NEVER combine an
            # overridden family with a foreign leaf's dialect string.
            dialect = actual_dialect if actual_family == resolved_backend else None
        else:
            resolved_backend = (
                actual_family if actual_family is not None else CONST_BACKEND.POLARS
            )
            dialect = actual_dialect

        relation_system_cls = get_relation_system(resolved_backend)
        relation_system = relation_system_cls(dialect=dialect)
        expression_system_cls = get_expression_system(resolved_backend)
        expression_system = expression_system_cls(dialect=dialect)
        expr_visitor = UnifiedExpressionVisitor(expression_system)

        # Item 97 (inherits item 92's Revision 4 upfront guard, broadened to
        # ANY foreign-family ref -- bare or derived -- not just a bare
        # ReadRelNode root): a lazy narwhals ANCHOR consuming foreign refs
        # must reject before caching -- _coerce_to_match's eager-over-lazy
        # handling is order-dependent and must not be relied upon.
        if backend_target_name is not None or ref_names:
            anchor_name = backend_target_name or sorted(ref_names)[0]
            anchor_family, _, anchor_leaf = self._resolve_identity_leaf(anchor_name)
            if anchor_leaf is not None and _is_lazy_narwhals(anchor_leaf.dataframe):
                if any(
                    self._resolve_actual_identity_for(n)[0]
                    not in (None, resolved_backend)
                    for n in ref_names
                ):
                    raise TypeError(
                        "Cross-family DAG coercion is not supported with a lazy Narwhals anchor."
                    )

        canonical: dict[str, "tuple[Any, CONST_BACKEND | None, str | None]"] = {}
        coerced: dict[tuple[str, CONST_BACKEND, str | None], Any] = {}

        def resolver(n: str) -> Any:
            value, src_family, src_dialect = canonical[n]
            if src_family is None:
                return value  # no-leaf ref: already anchor-family
            cons_family = visitor.backend.backend_type
            cons_dialect = visitor.backend.dialect
            needs_coercion = (
                src_family != cons_family
                or (
                    src_family is CONST_BACKEND.NARWHALS
                    and src_dialect != cons_dialect
                )
            )
            if not needs_coercion:
                return value
            key = (n, cons_family, cons_dialect)
            if key not in coerced:
                proto = _consumer_prototype(cons_family, cons_dialect)
                coerced[key] = UnifiedRelationVisitor._coerce_to_match(proto, value)
            return coerced[key]

        # KeyDriftContext (item 48 PR-D): +1 optional visitor param,
        # analogous to ref_resolver. The context's resource_name is the
        # apply_conform() fallback "child" identity for nodes that carry no
        # resource_name of their own (a bare ConformRelNode; a
        # ResourceReadRelNode always supplies its own Frictionless name).
        #
        # backend_target_name and key_target_name are deliberately separate
        # params (PR-2 Sec 2.2): backend_target_name governs backend
        # DETECTION only (which relation's leaf ReadRelNode to inspect) and
        # is set even for an ad-hoc execute() target, purely so an
        # arbitrary alphabetically-first dependency can anchor detection.
        # key_target_name governs the TARGET's key-context IDENTITY only.
        # Conflating the two previously misattributed an ad-hoc execute()
        # target's key assessment to that same alphabetically-first
        # dependency's FK constraints. key_target_name is None for
        # execute() (no DAG identity to assess an ad-hoc relation against)
        # and set to the real name for collect()/collect_with_drift(), so
        # key_context stays None for ad-hoc targets (frame-level,
        # key_changes stays None -- not assessed) and correct for named
        # targets. The dependency loop below always builds each
        # dependency's OWN context regardless of the target's identity
        # (including when it's None), so a bare-conformed dependency is
        # NEVER assessed against the TARGET's FK constraints — avoiding
        # both the original misattribution and a wrong report / spurious
        # freeze for the dependency itself.
        key_context = None
        if key_target_name is not None:
            from mountainash.relations.dag.key_context import KeyDriftContext

            key_context = KeyDriftContext(
                resource_name=key_target_name,
                constraints_for=self.constraints_for,
                schema_of=self.schema,
            )

        visitor = UnifiedRelationVisitor(
            relation_system,
            expression_visitor=expr_visitor,
            ref_resolver=resolver,
            key_context=key_context,
            identity_resolver=lambda name: self.relations[name]._node,
        )

        # Compile refs in topological order
        if ref_names:
            from mountainash.relations.dag.key_context import KeyDriftContext

            # Item 97: canonical materialization -- every ref is compiled
            # exactly once, with ITS OWN (family, dialect) identity, and
            # stored as (value, family, dialect) in `canonical`. A consumer
            # of that ref coerces it lazily via `resolver()` above (memoised
            # per (name, consumer_family, consumer_dialect)). This replaces
            # item 89's four-way branch (anchor-for-foreign-bare-read /
            # own-dialect / reuse-anchor) with a three-way branch that still
            # reuses the anchor's objects for the same-family-same-dialect
            # case (item 89's zero-cost homogeneous-DAG path).
            full_order = self.topological_order(target=None)
            for n in full_order:
                if n not in ref_names:
                    continue
                rel = self.relations[n]
                root = getattr(rel, "_node", None)
                if root is None:
                    raise ValueError(f"relation {n!r} has no _node attribute")

                ref_family, ref_dialect = self._resolve_actual_identity_for(n)
                checks_start = len(visitor.residue_checks)
                trace_counts = {
                    key: len(trace.records)
                    for key, trace in visitor.diagnostic_traces.items()
                }

                # Each dependency is key-assessed against ITS OWN
                # constraints, unconditionally -- including a no-leaf
                # SourceRelNode ref -- independent of whether the target
                # itself has a key identity.
                visitor.key_context = KeyDriftContext(
                    resource_name=n,
                    constraints_for=self.constraints_for,
                    schema_of=self.schema,
                )

                if ref_family is None:
                    # No physical read identity (pure SourceRelNode/inline-
                    # data ref). Materialise with the anchor pair.
                    visitor.backend, visitor.expr_visitor = (
                        relation_system,
                        expr_visitor,
                    )
                    compiled = root.accept(visitor)
                    canonical[n] = (compiled, None, None)
                elif ref_family == resolved_backend and ref_dialect == dialect:
                    # Same family + same dialect as the anchor: reuse the
                    # anchor's ORIGINAL objects (item 89's zero-cost path).
                    visitor.backend, visitor.expr_visitor = (
                        relation_system,
                        expr_visitor,
                    )
                    compiled = root.accept(visitor)
                    canonical[n] = (compiled, ref_family, ref_dialect)
                else:
                    # Foreign family, or same family with a different
                    # dialect: compile with the ref's OWN (family, dialect)
                    # identity -- never the anchor's -- so a dialect-scoped
                    # CapabilityFact gates/enriches correctly, and store the
                    # raw canonical value uncoerced; coercion happens lazily
                    # at resolver() call time, against the ACTUAL consumer.
                    visitor.backend = get_relation_system(ref_family)(dialect=ref_dialect)
                    visitor.expr_visitor = UnifiedExpressionVisitor(
                        get_expression_system(ref_family)(dialect=ref_dialect)
                    )
                    compiled = root.accept(visitor)
                    canonical[n] = (compiled, ref_family, ref_dialect)

                dependency_checks = visitor.residue_checks[checks_start:]
                dep_family = getattr(visitor.backend, "backend_type", None)
                dep_dialect = getattr(visitor.backend, "dialect", None)
                dep_trace = visitor.diagnostic_traces.get((dep_family, dep_dialect))
                dep_trace_records = ()
                if dep_trace is not None:
                    dep_trace_records = dep_trace.records[
                        trace_counts.get((dep_family, dep_dialect), 0):
                    ]
                if dependency_checks or dep_trace_records:
                    from types import SimpleNamespace

                    from mountainash.core.limitations import enrich_materialization
                    from mountainash.relations.core.relation_api.relation import (
                        _materialize,
                    )
                    from mountainash.core.types import (
                        is_ibis_table,
                        is_narwhals_lazyframe,
                        is_polars_lazyframe,
                    )

                    scoped_trace = (
                        SimpleNamespace(records=dep_trace_records)
                        if dep_trace_records
                        else None
                    )
                    original = compiled
                    compiled = enrich_materialization(
                        visitor.backend,
                        lambda: _materialize(compiled, unwrap=False),
                        diagnostic_trace=scoped_trace,
                        residue_checks=dependency_checks,
                    )
                    if is_ibis_table(original) and not is_ibis_table(compiled):
                        import ibis
                        compiled = ibis.memtable(compiled)
                    if is_polars_lazyframe(original) or is_narwhals_lazyframe(original):
                        compiled = compiled.lazy()
                    if dep_trace is not None and dep_trace_records:
                        consumed = {id(record) for record in dep_trace_records}
                        dep_trace._records = [
                            record
                            for record in dep_trace._records
                            if id(record) not in consumed
                        ]
                    del visitor.residue_checks[checks_start:]
                    canonical[n] = (compiled, ref_family, ref_dialect)

            # Restore the anchor's ORIGINAL backend/expr_visitor/key_context
            # ONCE, after the loop -- never per-branch (a trailing no-leaf
            # ref must not leak its key_context into the target compile).
            visitor.backend, visitor.expr_visitor, visitor.key_context = (
                relation_system,
                expr_visitor,
                key_context,
            )

        # Compile the target node itself
        return node.accept(visitor), visitor

    def schema(
        self, name: str
    ) -> dict[str, "MountainashDtype | SchemaTypeStatus"]:
        """Return the inferred output schema for a named relation.

        Values are canonical ``MountainashDtype`` where inferable, or a
        ``SchemaTypeStatus`` (UNKNOWN / UNCONSTRAINED) where not.
        """
        from mountainash.relations.dag.introspection import schema

        return schema(self, name)

    def describe(self) -> dict[str, dict]:
        """Return a structural summary of every registered relation."""
        from mountainash.relations.dag.introspection import describe

        return describe(self)

    def to_dot(self) -> str:
        """Return a Graphviz DOT string of the DAG structure."""
        from mountainash.relations.dag.introspection import to_dot

        return to_dot(self)

    def to_package(self, *, strict: bool = False) -> Any:
        """Export this DAG as a Frictionless DataPackage descriptor.

        Emits a resource for every named tabular relation: a ResourceReadRelNode
        reuses its original DataResource; any other relation derives its schema via
        the ref-resolved dag.schema(name) and emits best-effort (schema-less when no
        columns are determinable). Assets pass through unchanged.

        Default is non-fatal (principle best-effort-introspection R3). strict=True
        raises MissingResourceSchema for any relation whose schema is empty or
        contains a genuinely-UNKNOWN column (R4)."""
        from mountainash.relations.dag.packaging import to_package

        return to_package(self, strict=strict)

    # ------------------------------------------------------------------
    # DAG-level validation
    # ------------------------------------------------------------------

    def validate(
        self,
        specs: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        backend: Optional[str] = None,
        failure_sample: Optional[int] = None,
        allow_imperfect_key: bool = False,
    ) -> "DAGValidationResult":
        """Full validation via the backend-agnostic ValidationRunner.

        Per-resource checks compile from each spec/contract; FK row-integrity
        checks are generated from constraint_metadata + spec foreign keys by
        validation.fk.build_fk_checks and compiled as relation anti-joins.
        A resource's invalid keyed identity is isolated into that resource's
        own failing result (check_id="__identity__") rather than raised out
        of this call - every other resource still validates (spec item 8j §3.2).
        """
        from mountainash.relations.dag.validation import validate

        return validate(
            self, specs, context=context, backend=backend, failure_sample=failure_sample,
            allow_imperfect_key=allow_imperfect_key,
        )

    def validate_quick(
        self,
        specs: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
        backend: Optional[str] = None,
        failure_sample: Optional[int] = None,
        allow_imperfect_key: bool = False,
    ) -> "DAGValidationResult":
        """Fast validation via the ValidationRunner (fail_fast=True; identical shapes)."""
        from mountainash.relations.dag.validation import validate_quick

        return validate_quick(
            self, specs, context=context, backend=backend, failure_sample=failure_sample,
            allow_imperfect_key=allow_imperfect_key,
        )

    def _unknown_ref_error(self, missing: str) -> "UnknownRelationRef":
        """Unified missing-upstream error, naming registered dependents."""
        from mountainash.relations.dag.errors import UnknownRelationRef

        dependents = sorted(d for (u, d) in self.dependency_edges if u == missing)
        referenced_by = (
            ", ".join(repr(d) for d in dependents)
            if dependents
            else "an unregistered relation"
        )
        return UnknownRelationRef(
            f"relation {missing!r} referenced but not in DAG "
            f"(referenced by {referenced_by})"
        )

    def _resolve_actual_identity_for(
        self, target_name: str
    ) -> "tuple[CONST_BACKEND | None, str | None]":
        """Detected physical ``(family, dialect)`` for ``target_name``'s own
        dependency tree, walking in the SAME topological/ancestor order the
        two independent resolvers below used historically (so both keep
        resolving from the same leaf), but in ONE walk making exactly ONE
        :func:`identify_backend_identity` probe per candidate leaf --
        replacing the previous two independent walks (one via
        ``identify_backend``, one via ``identify_backend_identity``) that
        duplicated detection for no reason (round-2 finding:
        ``identify_backend_identity`` already calls ``identify_backend``
        internally).

        Deliberately IGNORES any explicit ``backend=`` override -- the
        override is an execution request, not evidence about a ref's own
        physical identity. Per-ref/anchor guards that need to detect
        "would an override create an invalid hybrid" must call this
        directly rather than the override-honouring
        ``_resolve_backend_const`` wrapper below.

        Returns a 3-way taxonomy distinguishing "no physical read at all"
        from "physical read, unresolved dialect" (round-1 finding: the
        old two-resolver approach collapsed both to ``dialect=None``,
        conflating "inherit the anchor unconditionally" with "this ref
        genuinely has an unknown dialect"):
          ``(None, None)``      -- no readable leaf (pure SourceRelNode
                                    tree, or every candidate failed
                                    detection)
          ``(family, None)``    -- a readable leaf was found, but its
                                    dialect is genuinely unbound/unknown
                                    (e.g. an unbound Ibis table)
          ``(family, dialect)`` -- fully resolved
        """
        from mountainash.relations.core.relation_api.relation_base import (
            RelationBase,
        )
        from mountainash.core.backend_detection import identify_backend_identity
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
                # Node type not handled, or this candidate's own root is
                # itself a bare RefRelNode with no direct physical leaf --
                # skip, try the next candidate in topological order.
                continue
            if read_node is not None:
                try:
                    identity = identify_backend_identity(read_node.dataframe)
                    return identity.family, identity.dialect
                except Exception:
                    pass
        return None, None

    def _resolve_identity_leaf(
        self, target_name: str
    ) -> "tuple[CONST_BACKEND | None, str | None, Any | None]":
        """Return the identity and leaf selected for a named relation."""
        from mountainash.relations.core.relation_api.relation_base import RelationBase
        from mountainash.core.backend_detection import identify_backend_identity
        from mountainash.relations.dag.errors import RelationDAGRequired

        for n in self.topological_order(target=target_name):
            root = getattr(self.relations[n], "_node", None)
            if root is None:
                continue
            try:
                read_node = RelationBase._find_leaf_read_node(root)
            except (ValueError, AttributeError, RelationDAGRequired):
                continue
            if read_node is not None:
                try:
                    identity = identify_backend_identity(read_node.dataframe)
                    return identity.family, identity.dialect, read_node
                except Exception:
                    pass
        return None, None, None

    def _resolve_actual_identity_for_node(
        self, node: Any
    ) -> "tuple[CONST_BACKEND | None, str | None]":
        """Sibling of :meth:`_resolve_actual_identity_for` for the ad-hoc
        (non-named) ``execute()`` case: a single leaf probe on ``node``
        itself -- there is no registered relation name to walk via
        :meth:`topological_order`, so this inspects only ``node``'s own
        leaf directly."""
        from mountainash.relations.core.relation_api.relation_base import (
            RelationBase,
        )
        from mountainash.core.backend_detection import identify_backend_identity
        from mountainash.relations.dag.errors import RelationDAGRequired

        try:
            read_node = RelationBase._find_leaf_read_node(node)
        except (ValueError, AttributeError, RelationDAGRequired):
            return None, None
        if read_node is None:
            return None, None
        try:
            identity = identify_backend_identity(read_node.dataframe)
            return identity.family, identity.dialect
        except Exception:
            return None, None

    def _resolve_backend_const(
        self, backend: Optional[str], target_name: str
    ) -> CONST_BACKEND:
        """Determine the CONST_BACKEND to use for compilation.

        If ``backend`` is given explicitly, honour it -- this is the ONE
        caller-facing entry point that still applies the override;
        internal per-ref/anchor guards needing the override-independent
        physical family must call :meth:`_resolve_actual_identity_for`
        directly. Otherwise walk ``target_name``'s dependency tree for its
        detected physical family, falling back to Polars when no
        ReadRelNode is found (e.g. pure SourceRelNode / inline data trees).
        """
        if backend is not None:
            try:
                return CONST_BACKEND(backend.lower())
            except ValueError:
                raise ValueError(f"unknown backend: {backend!r}")
        family, _dialect = self._resolve_actual_identity_for(target_name)
        return family if family is not None else CONST_BACKEND.POLARS

    def _resolve_dialect_for(self, target_name: str) -> Optional[str]:
        """Dialect for the first ReadRelNode found while walking
        ``target_name``'s dependency tree -- same anchor-selection order
        as :meth:`_resolve_backend_const`, so family and dialect are
        always resolved from the same leaf. Unlike backend-family
        resolution, dialect is *not* determinable from an explicit
        ``backend=`` string override, so this always walks regardless.
        Returns ``None`` when no ReadRelNode is found, or when one is
        found but its dialect is genuinely unbound/unknown.
        """
        _family, dialect = self._resolve_actual_identity_for(target_name)
        return dialect
