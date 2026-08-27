"""Shared DAG materialization session (spec section 10, Task 7).

Graph-level orchestration over :func:`materialize_native`. ``RelationDAG``
remains the public owner and entry point; ``RelationDAG._compile_with_refs()``
delegates cache and resolver mechanics to :class:`DAGMaterializationSession`
so a named resource is compiled and materialized exactly once per session,
shared across every consumer (dependency of a collected target, a
validation rule, a foreign-key resolver, ...) instead of re-executing the
whole query plan once per consumer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.materialization import (
    ExecutionForm,
    MaterializationPurpose,
    MaterializationScope,
    NativeExecutionValue,
    diagnostic_polars_view,
    materialize_native,
)
from mountainash.relations.dag.traversal import walk_refs as _walk_refs

if TYPE_CHECKING:
    from mountainash.core.capabilities.identity import BackendIdentity
    from mountainash.relations.core.materialization import DiagnosticFrameView
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.relations.dag.dag import RelationDAG
    from mountainash.relations.dag.key_context import KeyDriftContext

__all__ = [
    "CanonicalEntry",
    "DAGMaterializationSession",
]


def _anchor_prototype(family: CONST_BACKEND, dialect: "str | None") -> Any:
    """A lightweight empty object of *family* for coercion to target."""
    from mountainash.core.transit import BoundaryKey, transit_call

    if family is CONST_BACKEND.POLARS:
        import polars as pl

        return pl.DataFrame({}).lazy()
    if family is CONST_BACKEND.IBIS:
        import ibis

        return transit_call(BoundaryKey.DAG_PROTOTYPE_ADAPTER, ibis.memtable, {})
    if family is CONST_BACKEND.NARWHALS:
        import narwhals as nw

        if dialect == "narwhals-polars":
            import polars as pl

            return transit_call(
                BoundaryKey.DAG_PROTOTYPE_ADAPTER, nw.from_native, pl.DataFrame({}), eager_only=True
            )
        if dialect == "narwhals-pyarrow":
            import pyarrow as pa

            return transit_call(
                BoundaryKey.DAG_PROTOTYPE_ADAPTER, nw.from_native, pa.table({}), eager_only=True
            )
        import pandas as pd

        pandas_empty = transit_call(BoundaryKey.PYDATA_EXPLICIT_PANDAS_INPUT, pd.DataFrame, {})
        return transit_call(
            BoundaryKey.DAG_PROTOTYPE_ADAPTER, nw.from_native, pandas_empty, eager_only=True
        )
    return None


def _consumer_prototype(family: CONST_BACKEND, dialect: "str | None") -> Any:
    """Alias for :func:`_anchor_prototype` (the consumer-side prototype
    reuses the exact same construction the anchor-side already used --
    without rewriting item 92's territory)."""
    return _anchor_prototype(family, dialect)


def _is_lazy_narwhals(obj: Any) -> bool:
    """True iff *obj* is a narwhals LazyFrame."""
    try:
        import narwhals as nw

        return isinstance(obj, nw.LazyFrame)
    except Exception:
        return False


def _resolve_backend_and_dialect(
    actual_family: "CONST_BACKEND | None",
    actual_dialect: "str | None",
    backend: "str | None",
) -> "tuple[CONST_BACKEND, str | None]":
    """Combine a detected physical ``(family, dialect)`` with an optional
    explicit ``backend=`` override into one coherent resolved pair.

    The dialect is trusted only when it was actually detected on a leaf
    belonging to the resolved (possibly overridden) family -- never an
    overridden family combined with a foreign leaf's dialect string.
    Polars is the one exception: it has exactly one dialect, so an
    override or fallback to Polars always yields dialect ``"polars"``,
    never an unnecessarily lossy ``None``.
    """
    if backend is not None:
        try:
            resolved = CONST_BACKEND(backend.lower())
        except ValueError:
            raise ValueError(f"unknown backend: {backend!r}") from None
        if resolved is CONST_BACKEND.POLARS:
            return resolved, "polars"
        return resolved, (actual_dialect if actual_family == resolved else None)
    resolved = actual_family if actual_family is not None else CONST_BACKEND.POLARS
    if actual_dialect is not None:
        return resolved, actual_dialect
    return resolved, ("polars" if resolved is CONST_BACKEND.POLARS else None)


@dataclass(frozen=True)
class CanonicalEntry:
    """One named resource's canonical materialization (spec 10.2)."""

    native: NativeExecutionValue
    diagnostic_records: "tuple[Any, ...]"
    residue_checks: "tuple[Any, ...]"
    residue_check_nodes: "Mapping[str, str]"
    key_context: "KeyDriftContext | None"


class DAGMaterializationSession:
    """Compiles and caches every DAG resource required by one session.

    The canonical cache has one entry per named resource, keyed by
    resource name; each is compiled exactly once, in the order it is
    first required. The coercion cache is keyed by
    ``(resource_name, consumer_family, consumer_dialect)`` (spec 10.3):
    a consumer whose active visitor identity differs from a resource's
    canonical identity gets a declared-adapter coercion, memoized so a
    resource consumed by N differently-identified consumers is coerced
    at most once per distinct consumer identity, never once per consumer.

    ``isolate_failures`` is unused by this class directly -- consumed by
    DAG validation (Task 8), which needs a failed resource to degrade to
    a typed failure state rather than raising out of the session.
    """

    def __init__(
        self,
        dag: "RelationDAG",
        *,
        backend: "str | None" = None,
        isolate_failures: bool = False,
    ) -> None:
        self.dag = dag
        self.backend = backend
        self.isolate_failures = isolate_failures
        self._canonical: "dict[str, CanonicalEntry]" = {}
        self._coerced: "dict[tuple[str, CONST_BACKEND, str | None], NativeExecutionValue]" = {}
        self._diagnostic_views: "dict[str, DiagnosticFrameView]" = {}
        self._visitors: "dict[str, UnifiedRelationVisitor]" = {}
        self._scope = MaterializationScope()
        self._closed = False

    @property
    def canonical_keys(self) -> "frozenset[str]":
        return frozenset(self._canonical)

    @property
    def coercion_keys(self) -> "frozenset[tuple[str, CONST_BACKEND, str | None]]":
        return frozenset(self._coerced)

    @property
    def cached_values(self) -> "tuple[Any, ...]":
        """Every raw native value currently cached (canonical + coerced).

        Never a :class:`~mountainash.relations.core.materialization.DiagnosticFrameView`
        -- diagnostic views live in a separate mapping the ref resolver
        can never read (spec 10.4's type-separation guarantee).
        """
        values = [entry.native.value for entry in self._canonical.values()]
        values.extend(coerced.value for coerced in self._coerced.values())
        return tuple(values)

    def _resolve_identity(
        self, name: str, *, honor_override: bool
    ) -> "tuple[CONST_BACKEND, str | None]":
        actual_family, actual_dialect = self.dag._resolve_actual_identity_for(name)
        backend = self.backend if honor_override else None
        return _resolve_backend_and_dialect(actual_family, actual_dialect, backend)

    def _compile_named(self, name: str, *, honor_override: bool = False) -> CanonicalEntry:
        """Compile and cache *name*'s canonical materialization (spec 10.2).

        A no-op re-lookup when *name* is already canonical -- the session's
        entire value proposition is that this only actually compiles once.
        """
        if name in self._canonical:
            return self._canonical[name]
        if name not in self.dag.relations:
            raise self.dag._unknown_ref_error(name)

        rel = self.dag.relations[name]
        root = getattr(rel, "_node", None)
        if root is None:
            raise ValueError(f"relation {name!r} has no _node attribute")

        resolved_backend, dialect = self._resolve_identity(name, honor_override=honor_override)

        # Item 97: a lazy Narwhals anchor consuming a foreign-family ref
        # must reject before caching -- _coerce_to_match's eager-over-lazy
        # handling is order-dependent and must not be relied upon. Scoped
        # to this resource's own direct refs; a foreign family reached
        # transitively through an intermediate dependency is caught when
        # THAT dependency's own _compile_named() runs this same check.
        _anchor_family, _, anchor_leaf = self.dag._resolve_identity_leaf(name)
        own_refs = _walk_refs(root)
        if anchor_leaf is not None and _is_lazy_narwhals(anchor_leaf.dataframe):
            if any(
                self.dag._resolve_actual_identity_for(ref_name)[0]
                not in (None, resolved_backend)
                for ref_name in own_refs
            ):
                raise TypeError(
                    "Cross-family DAG coercion is not supported with a lazy Narwhals anchor."
                )

        from mountainash.core.limitations import enrich_materialization
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
        from mountainash.relations.dag.key_context import KeyDriftContext

        relation_system = get_relation_system(resolved_backend)(dialect=dialect)
        expr_visitor = UnifiedExpressionVisitor(
            get_expression_system(resolved_backend)(dialect=dialect)
        )
        # Every dependency is key-assessed against ITS OWN constraints,
        # unconditionally -- including a no-leaf ref -- regardless of
        # whether it is the session's top-level requested name or a
        # transitively-required dependency (spec 10.5/item 48 PR-D).
        key_context = KeyDriftContext(
            resource_name=name,
            constraints_for=self.dag.constraints_for,
            schema_of=self.dag.schema,
        )

        def ref_resolver(ref_name: str) -> Any:
            return self.resolve(ref_name, resolved_backend, dialect)

        visitor = UnifiedRelationVisitor(
            relation_system,
            expression_visitor=expr_visitor,
            ref_resolver=ref_resolver,
            key_context=key_context,
            identity_resolver=lambda n: self.dag.relations[n]._node,
        )

        checks_start = len(visitor.residue_checks)
        compiled = root.accept(visitor)
        residue_checks_this = tuple(visitor.residue_checks[checks_start:])
        del visitor.residue_checks[checks_start:]

        from mountainash.core.backend_detection import identify_backend_identity
        from mountainash.core.capabilities.identity import BackendIdentity
        from mountainash.core.types import (
            is_ibis_table,
            is_narwhals_lazyframe,
            is_polars_lazyframe,
        )

        compiler_identity = BackendIdentity(resolved_backend, dialect)
        trace = visitor._active_diagnostic_trace()
        was_lazy = is_polars_lazyframe(compiled) or is_narwhals_lazyframe(compiled)

        if is_ibis_table(compiled):
            # DAG_CANONICAL's whole point (spec 10.2): a shared Ibis
            # resource is forced eager via ONE .cache() call, so every
            # later consumer within this session reuses it instead of
            # re-executing the query.
            def _thunk() -> NativeExecutionValue:
                return materialize_native(
                    compiled, compiler_identity, MaterializationPurpose.DAG_CANONICAL,
                    scope=self._scope,
                )

            native = enrich_materialization(
                visitor.backend, _thunk,
                diagnostic_trace=trace, residue_checks=residue_checks_this,
            )
        elif residue_checks_this or (trace is not None and trace.records):
            # Polars/Narwhals: materialize only as a vehicle to trigger
            # enrich_materialization's residue-check enrichment, then
            # restore the ORIGINAL lazy/eager shape -- the canonical
            # cache stays lazy for Polars/Narwhals (dag.collect()'s
            # documented lazy-when-possible contract; Polars' own
            # optimizer handles shared-subexpression reuse without a
            # forced eager cache, unlike Ibis).
            def _thunk() -> NativeExecutionValue:
                return materialize_native(
                    compiled, compiler_identity, MaterializationPurpose.DAG_CANONICAL,
                    scope=self._scope,
                )

            forced = enrich_materialization(
                visitor.backend, _thunk,
                diagnostic_trace=trace, residue_checks=residue_checks_this,
            )
            if was_lazy:
                relazified = forced.value.lazy()
                native = NativeExecutionValue(
                    relazified, forced.compiler_identity,
                    identify_backend_identity(relazified),
                    ExecutionForm.LAZY,
                )
            else:
                native = forced
        else:
            # No residue to enrich -- cache the raw compiled value as-is
            # (possibly still lazy), only detecting its identity.
            value_identity = identify_backend_identity(compiled)
            form = ExecutionForm.LAZY if was_lazy else ExecutionForm.EAGER
            native = NativeExecutionValue(compiled, compiler_identity, value_identity, form)

        diagnostic_records = tuple(getattr(trace, "records", ()))

        entry = CanonicalEntry(
            native=native,
            diagnostic_records=diagnostic_records,
            residue_checks=residue_checks_this,
            residue_check_nodes=dict(visitor.residue_check_nodes),
            key_context=key_context,
        )
        self._canonical[name] = entry
        self._visitors[name] = visitor
        return entry

    def compile_registered(
        self, name: str
    ) -> "tuple[NativeExecutionValue, UnifiedRelationVisitor]":
        """Compile a DAG-registered resource, materializing every
        transitively-required dependency exactly once along the way."""
        entry = self._compile_named(name, honor_override=True)
        return entry.native, self._visitors[name]

    def resolve(
        self,
        name: str,
        consumer_family: CONST_BACKEND,
        consumer_dialect: "str | None",
    ) -> Any:
        """The raw native value for *name*, coerced to match a consumer's
        active identity if needed (spec 10.3), memoized per distinct
        ``(name, consumer_family, consumer_dialect)`` triple."""
        entry = self._compile_named(name)
        native = entry.native
        src_family = native.value_identity.family
        src_dialect = native.value_identity.dialect
        if src_family is None:
            return native.value  # no-leaf ref: already anchor-family
        needs_coercion = src_family != consumer_family or (
            src_family is CONST_BACKEND.NARWHALS and src_dialect != consumer_dialect
        )
        if not needs_coercion:
            return native.value

        key = (name, consumer_family, consumer_dialect)
        if key not in self._coerced:
            from mountainash.relations.core.unified_visitor.relation_visitor import (
                UnifiedRelationVisitor,
            )

            proto = _consumer_prototype(consumer_family, consumer_dialect)
            coerced_value = UnifiedRelationVisitor._coerce_to_match(proto, native.value)
            destination_identity = self._destination_identity(
                consumer_family, consumer_dialect
            )
            self._coerced[key] = NativeExecutionValue(
                coerced_value, native.value_identity, destination_identity, ExecutionForm.EAGER
            )
        return self._coerced[key].value

    @staticmethod
    def _destination_identity(
        consumer_family: CONST_BACKEND, consumer_dialect: "str | None"
    ) -> "BackendIdentity":
        from mountainash.core.capabilities.identity import BackendIdentity

        return BackendIdentity(consumer_family, consumer_dialect)

    def diagnostic_view(self, name: str) -> "DiagnosticFrameView | None":
        """A read-only Polars view of *name*'s canonical value for result
        transport only (spec 10.4). Lives in a separate mapping the
        ``ref_resolver`` can never read -- never returned to execution,
        stored in a relation leaf, or fed back into ``resolve()``."""
        if name in self._diagnostic_views:
            return self._diagnostic_views[name]
        entry = self._canonical.get(name)
        if entry is None:
            return None
        view = diagnostic_polars_view(entry.native)
        self._diagnostic_views[name] = view
        return view

    def close(self, release_owned: bool) -> None:
        """Discard the session. *release_owned* controls whether its
        ``MaterializationScope`` (Ibis ``.cache()`` releases) actually
        runs: ``False`` for ordinary collection (spec 10.5 -- never
        release a value referenced by the returned native expression
        graph), ``True`` for a validation session (the sole release
        owner for its canonical native caches)."""
        if self._closed:
            return
        self._closed = True
        if release_owned:
            self._scope.close()
