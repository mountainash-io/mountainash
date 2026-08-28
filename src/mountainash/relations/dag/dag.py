
from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
from mountainash.relations.dag.traversal import walk_refs as _walk_refs


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


def _force_eager(value: Any, *, unwrap: bool) -> Any:
    """Force a lazy Polars/Narwhals value eager for residue enrichment
    (spec section 13, Task 10). Replaces the deleted
    ``Relation._materialize()`` -- the collection contract stays identical
    (Polars/Narwhals lazy -> eager; ``unwrap`` additionally converts an
    eager Narwhals frame to its native value, pandas included when the
    source itself was pandas-selected), but every conversion now routes
    through a literal, census-tracked ``transit_call()``.
    """
    from mountainash.core.backend_detection import narwhals_dialect
    from mountainash.core.transit import BoundaryKey, transit_call
    from mountainash.core.types import (
        is_narwhals_dataframe,
        is_narwhals_lazyframe,
        is_polars_lazyframe,
    )

    if is_polars_lazyframe(value):
        return transit_call(BoundaryKey.POLARS_LAZY_COLLECT, value.collect)
    if is_narwhals_lazyframe(value):
        value = transit_call(BoundaryKey.NARWHALS_LAZY_COLLECT, value.collect)
    if unwrap and is_narwhals_dataframe(value):
        if narwhals_dialect(value) == "narwhals-pandas":
            return transit_call(BoundaryKey.NARWHALS_NATIVE_UNWRAP_PANDAS, value.to_native)
        return transit_call(BoundaryKey.NARWHALS_NATIVE_UNWRAP_NON_PANDAS, value.to_native)
    return value

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
        from mountainash.core.types import is_narwhals_lazyframe, is_polars_lazyframe

        original = result
        result = enrich_materialization(
            visitor.backend,
            lambda: _force_eager(result, unwrap=False),
            diagnostic_trace=visitor._active_diagnostic_trace(),
            residue_checks=visitor.residue_checks,
        )
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
        from mountainash.relations.schema_inference import _schema_from_dataframe
        from mountainash.core.limitations import enrich_materialization

        result, visitor = self._collect_with_visitor(name, backend=backend)
        frame = enrich_materialization(
            visitor.backend,
            lambda: _force_eager(result, unwrap=True),
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
        ``execute()``. Cache and resolver mechanics delegate to a fresh
        :class:`~mountainash.relations.dag.materialization.DAGMaterializationSession`
        (Task 7, spec section 10) -- every relation named in ``ref_names``
        is compiled and materialized exactly once, shared across every
        consumer, coerced to a consumer's active identity via a declared
        adapter and memoized per distinct consumer identity. Discarded
        without releasing owned native caches (spec 10.5: ordinary
        collection never releases a value referenced by the returned
        native expression graph) -- ``session.close(release_owned=False)``.

        Returns ``(result, visitor)`` — callers needing post-compile
        visitor state (e.g. ``collect_with_drift()``'s
        ``visitor.drift_reports``) can retrieve it without a second
        compilation pass.
        """
        missing_refs = sorted(n for n in ref_names if n not in self.relations)
        if missing_refs:
            raise self._unknown_ref_error(missing_refs[0])

        from mountainash.relations.dag.materialization import (
            DAGMaterializationSession,
            _is_lazy_narwhals,
            _resolve_backend_and_dialect,
            _SessionRefResolver,
        )

        session = DAGMaterializationSession(self, backend=backend)
        try:
            if key_target_name is not None:
                # collect()'s case: the target IS itself a registered
                # relation -- the session's own per-name compile handles
                # it (and every dependency it transitively requires)
                # directly; unwrap to the raw native value to preserve
                # this method's existing contract. compile_requested_native()
                # guards the target's own plans before any native-forcing
                # step (Task 9 step 6) when the session is
                # NATIVE_COLLECTION-moded; an intermediate dependency that
                # loses its transported field before this output is never
                # rejected, since only the target's own visitor is checked.
                native, visitor = session.compile_requested_native(key_target_name)
                # Each named resource compiled with its own dedicated
                # visitor (Task 7) -- collect_with_drift()'s caller reads
                # ONE visitor.drift_reports list, so prepend every
                # transitively-required dependency's own drift reports,
                # in the same topological (depth-first) order they were
                # produced, ahead of the target's own.
                dependency_drifts: "list[Any]" = []
                for dep_name in self.topological_order(target=key_target_name):
                    if dep_name == key_target_name:
                        continue
                    dep_visitor = session._visitors.get(dep_name)
                    if dep_visitor is not None:
                        dependency_drifts.extend(dep_visitor.drift_reports)
                visitor.drift_reports = dependency_drifts + visitor.drift_reports
                return native.value, visitor

            # execute()'s ad-hoc case: `node` is not a registered relation
            # (no session cache entry of its own), so resolve its identity
            # and compile it directly here, using the session only to
            # resolve its refs.
            from mountainash.expressions.core.expression_system.expsys_base import (
                get_expression_system,
            )
            from mountainash.expressions.core.unified_visitor import (
                UnifiedExpressionVisitor,
            )
            from mountainash.relations.core.relation_protocols.relsys_base import (
                get_relation_system,
            )
            from mountainash.relations.core.unified_visitor.relation_visitor import (
                UnifiedRelationVisitor,
            )

            if backend_target_name is not None:
                actual_family, actual_dialect = self._resolve_actual_identity_for(
                    backend_target_name
                )
            elif ref_names:
                anchor_name = sorted(ref_names)[0]
                actual_family, actual_dialect = self._resolve_actual_identity_for(
                    anchor_name
                )
            else:
                actual_family, actual_dialect = self._resolve_actual_identity_for_node(
                    node
                )
            resolved_backend, dialect = _resolve_backend_and_dialect(
                actual_family, actual_dialect, backend
            )

            # Item 97: a lazy Narwhals anchor consuming a foreign-family ref
            # must reject before caching.
            if backend_target_name is not None or ref_names:
                anchor_name = backend_target_name or sorted(ref_names)[0]
                _anchor_family, _, anchor_leaf = self._resolve_identity_leaf(anchor_name)
                if anchor_leaf is not None and _is_lazy_narwhals(anchor_leaf.dataframe):
                    if any(
                        self._resolve_actual_identity_for(n)[0]
                        not in (None, resolved_backend)
                        for n in ref_names
                    ):
                        raise TypeError(
                            "Cross-family DAG coercion is not supported with a lazy Narwhals anchor."
                        )

            relation_system = get_relation_system(resolved_backend)(dialect=dialect)
            expr_visitor = UnifiedExpressionVisitor(
                get_expression_system(resolved_backend)(dialect=dialect)
            )

            ref_resolver = _SessionRefResolver(session, resolved_backend, dialect)

            visitor = UnifiedRelationVisitor(
                relation_system,
                expression_visitor=expr_visitor,
                ref_resolver=ref_resolver,
                key_context=None,  # ad-hoc execute() target: no DAG identity to assess
                identity_resolver=lambda n: self.relations[n]._node,
            )
            return node.accept(visitor), visitor
        finally:
            session.close(release_owned=False)

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
