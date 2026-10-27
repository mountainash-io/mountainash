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

from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Mapping

from mountainash.core.constants import CONST_BACKEND
from mountainash.core.errors import BackendConversionError
from mountainash.relations.core.materialization import (
    ExecutionForm,
    MaterializationPurpose,
    MaterializationScope,
    NativeExecutionValue,
    diagnostic_polars_view,
    materialize_native,
)
from mountainash.relations.core.execution.preparation import ExecutionPhase
from mountainash.relations.dag.traversal import walk_refs as _walk_refs

if TYPE_CHECKING:
    from mountainash.conform.structured_transport import StructuredFieldPlanMap
    from mountainash.core.capabilities.capture import Environment
    from mountainash.core.capabilities.identity import BackendIdentity
    from mountainash.core.capabilities.policy import CapabilityPolicy, _ExecutionContext
    from mountainash.relations.core.materialization import DiagnosticFrameView
    from mountainash.relations.core.unified_visitor.relation_visitor import (
        UnifiedRelationVisitor,
    )
    from mountainash.relations.dag.dag import RelationDAG
    from mountainash.relations.dag.key_context import KeyDriftContext

__all__ = [
    "CanonicalEntry",
    "DAGMaterializationSession",
    "SessionMode",
]


def _anchor_prototype(family: CONST_BACKEND, dialect: "str | None") -> Any:
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

        pandas_empty = pd.DataFrame({})
        return nw.from_native(pandas_empty, eager_only=True)
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
    requested: Any = None,
) -> "tuple[CONST_BACKEND, str | None]":
    """Combine a detected physical ``(family, dialect)`` with an optional
    resolved ``target=`` location into one coherent resolved pair.

    The dialect is trusted only when it was actually detected on a leaf
    belonging to the resolved (possibly overridden) family -- never an
    overridden family combined with a foreign leaf's dialect string.
    Polars is the one exception: it has exactly one dialect, so an
    override or fallback to Polars always yields dialect ``"polars"``,
    never an unnecessarily lossy ``None``.
    """
    if requested is not None:
        resolved = requested.family
        if resolved is CONST_BACKEND.POLARS:
            return resolved, "polars"
        if requested.dialect is not None:
            return resolved, requested.dialect
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
    structured_field_plans: "StructuredFieldPlanMap"


class _SessionRefResolver:
    """One compiled resource's ``ref_resolver`` callable, plus a structured
    field plan side channel a downstream consumer can query without
    widening the visitor's one-parameter ``ref_resolver(name) -> Any``
    contract (Task 8, spec section 10).

    ``__call__`` returns only the native value, exactly like the closure
    it replaces -- ``structured_plans()`` is a SEPARATE method, never
    routed through ``__call__()`` or returned to execution.
    """

    def __init__(
        self,
        session: "DAGMaterializationSession",
        consumer_context: "_ExecutionContext | None" = None,
        destination: Any = None,
        requirement: Any = None,
        inherited: Any = None,
        placement: Any = None,
    ) -> None:
        self._session = session
        self._consumer_context = consumer_context
        self._destination = destination
        self._requirement = requirement
        self._inherited = inherited
        self._placement = placement

    def __call__(self, name: str) -> Any:
        if self._destination is not None:
            value = self._session.resolve_at(
                name, self._destination, self._requirement, self._inherited, self._placement,
            )
            self._destination = self._session._destination_for(self._destination)
            return value
        return self._session.resolve(name, self._consumer_context)

    def structured_plans(self, name: str) -> "StructuredFieldPlanMap":
        if self._destination is not None:
            resolved = self._session._resolved.get((name, self._destination.key))
            if resolved is not None:
                return resolved.metadata.structured_field_plans
            entry = self._session._canonical.get(name)
            if entry is not None:
                return entry.structured_field_plans
            bound = self._session._bound.get((name, self._destination.key))
            if bound is not None:
                return bound[1].structured_field_plans
        return self._session._compile_named(name).structured_field_plans

    def envelope(self, name: str) -> Any:
        """Consumer-bound metadata side channel; never returned as a ref value."""
        return self._session._resolved[(name, self._destination.key)]


class SessionMode(Enum):
    """A session's purpose (Task 9, spec section 10/18).

    ``NATIVE_COLLECTION`` (the default): the session backs
    :meth:`RelationDAG.collect`/:meth:`RelationDAG.collect_with_drift`. The
    requested resource's own compiled plans are inspected for an applied
    structured transport that still needs logical resolution before any
    physical result reaches the caller -- an intermediate dependency that
    loses its transported field before the requested output is never
    rejected.

    ``VALIDATION``: the session backs a :class:`DAGValidationContext`. A
    logical plan is expected and permitted; validation resolves it into a
    :class:`~mountainash.validation.prepared.PreparedValidationInput`
    rather than raising.
    """

    NATIVE_COLLECTION = "native_collection"
    VALIDATION = "validation"


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
        execution_policy: "CapabilityPolicy",
        target: Any = None,
        isolate_failures: bool = False,
        node_transforms: "Mapping[str, Callable[[Any], Any]] | None" = None,
        mode: SessionMode = SessionMode.NATIVE_COLLECTION,
    ) -> None:
        self.dag = dag
        self.target = target
        self.isolate_failures = isolate_failures
        self.mode = mode
        self._node_transforms = dict(node_transforms or {})
        self._execution_policy = execution_policy
        self._package_versions: "dict[str, str | None]" = {}
        self._canonical: "dict[str, CanonicalEntry]" = {}
        self._plans: dict[str, Any] = {}
        self._bound: dict[tuple[str, tuple], tuple[Any, Any]] = {}
        self._resolved: dict[tuple[str, tuple], Any] = {}
        self._coerced: "dict[tuple[str, tuple[CONST_BACKEND, str | None, int], Environment], NativeExecutionValue]" = {}
        self._diagnostic_views: "dict[str, DiagnosticFrameView]" = {}
        self._visitors: "dict[str, UnifiedRelationVisitor]" = {}
        self._validation_native: "dict[str, NativeExecutionValue]" = {}
        self._scope = MaterializationScope()
        self._closed = False
        self._execution_phase = ExecutionPhase.EXECUTE
        self._execution_tokens = None
        self._execution_transport = None
        self._execution_metadata = None

    @property
    def canonical_keys(self) -> "frozenset[str]":
        return frozenset(self._canonical) | frozenset(self._plans)

    @property
    def coercion_keys(self) -> "frozenset[tuple[str, tuple[CONST_BACKEND, str | None, int], Environment]]":
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
        values.extend(envelope.value for envelope, _ in self._bound.values())
        return tuple(values)

    def resolver_for(
        self, destination: Any, requirement: Any = None, inherited: Any = None,
        placement: Any = None,
    ) -> _SessionRefResolver:
        """Bind a ref resolver to this consumer's complete physical location.

        ``requirement`` is the prepared transfer recorded for the ref's
        ``/ref/<name>`` key, if its named plan does not already live there.
        ``inherited`` are the consumer plan's transfers beneath that key,
        re-keyed to the named plan's own root. ``placement`` is the location the
        consumer's preparation gave the named plan at that key.
        """
        return _SessionRefResolver(
            self, destination=destination, requirement=requirement, inherited=inherited,
            placement=placement,
        )

    def resolve_at(
        self, name: str, destination: Any, requirement: Any = None, inherited: Any = None,
        placement: Any = None,
    ) -> Any:
        """Resolve a named plan in its own location, then apply the prepared transfer for this consumer."""
        from mountainash.relations.core.execution.compilation import CompilationSession
        from mountainash.relations.core.execution.metadata import CompiledSubtree, CompilationMetadata
        from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
        from mountainash.relations.core.execution.metadata import MetadataSession
        from mountainash.relations.core.execution.preparation import prepare_execution
        from mountainash.relations.core.execution.transport import TransportSession
        from mountainash.relations.core.errors import UnresolvedExecutionLocationError
        from mountainash.relations.core.relation_nodes import ReadRelNode
        from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
        from mountainash.core.lazy_imports import import_ibis_expr_ops
        from mountainash.relations.dag.key_context import KeyDriftContext

        if name not in self.dag.relations:
            raise self.dag._unknown_ref_error(name)
        if self._execution_tokens is None:
            self._execution_tokens = IdentityTokens()
            self._execution_metadata = MetadataSession(self._execution_tokens)
            self._execution_transport = TransportSession(self._execution_tokens)
        destination = self._destination_for(destination)
        root = self._canonical_node(name)
        tokens = self._execution_tokens
        # A resource the consumer placed (bound Ibis connection or Narwhals) keeps
        # that placement: the named plan resolves against it, not a Polars default.
        from mountainash.core.constants import CONST_BACKEND
        placed = (placement if placement is not None and (
            (placement.family is CONST_BACKEND.IBIS and placement.connection is not None)
            or placement.family is CONST_BACKEND.NARWHALS) else None)
        named_resolver = LocationResolver(tokens, identity_resolver=self._canonical_node)
        location = named_resolver.resolve(root)
        if location.binding == "memory":
            placed = None  # a borrowed memory plan follows the consumer's binding below
        else:
            location = named_resolver.resolve(root, binding=placed)
        connectionless = location.binding == "memory"
        # Only pure ref aliases of an in-memory read carry the eager payload.
        # A unary transformation is a deferred Ibis plan and cannot borrow a
        # non-Ibis consumer as a physical execution connection.
        payload_root = root
        if connectionless:
            seen = {name}
            while isinstance(payload_root, RefRelNode):
                if payload_root.name in seen:
                    raise UnresolvedExecutionLocationError(
                        f"Cyclic relation reference {payload_root.name!r}", node_key=name,
                    )
                seen.add(payload_root.name)
                payload_root = self._canonical_node(payload_root.name)
        bare_memory = (connectionless and isinstance(payload_root, ReadRelNode)
                       and isinstance(payload_root.dataframe.op(), import_ibis_expr_ops().InMemoryTable))
        # Schema introspection compiles named dependencies; it never borrows
        # the eager payload as a substitute for compiling the registered plan.
        payload_transfer = (
            self._execution_phase is not ExecutionPhase.SCHEMA
            and bare_memory and destination.connection is None
        )
        source_location = location if payload_transfer or not connectionless else destination
        binding_key = (name, source_location.key)
        if binding_key not in self._bound:
            if payload_transfer:
                envelope = CompiledSubtree(
                    payload_root.dataframe, location, tokens.token(payload_root), CompilationMetadata(),
                    reusable_lowering=True, repeatable_result=True,
                )
                visitor = None
            else:
                prepared = prepare_execution(
                    root, phase=self._execution_phase,
                    identity_resolver=self._canonical_node,
                    tokens=tokens, binding=destination if connectionless else placed,
                    inherited=inherited,
                )
                from mountainash.relations.core.owned_copy import assert_prepared_owned_open
                assert_prepared_owned_open(prepared)
                if self._execution_phase is ExecutionPhase.EXECUTE and not connectionless:
                    from mountainash.relations.core.owned_copy import require_copy_idle

                    require_copy_idle(prepared.locations[prepared.root_key].connection)
                from mountainash.relations.dag.introspection import structural_schema
                key_context = KeyDriftContext(
                    resource_name=name, constraints_for=self.dag.constraints_for,
                    schema_of=lambda ref_name: structural_schema(self.dag, ref_name),
                )
                compilation = CompilationSession(
                    prepared, ref_resolver_factory=self.resolver_for,
                    key_context=key_context, transport=self._execution_transport,
                    metadata=self._execution_metadata,
                )
                envelope, visitor = compilation.compile_root()
                if self._execution_phase is ExecutionPhase.EXECUTE and not connectionless:
                    envelope = self.cache_root(name, envelope, visitor)
            # Named bindings reuse the lowered plan. Only an actual capture
            # grants reusable rows; an opaque deferred plan remains deferred.
            envelope = replace(envelope, reusable_lowering=True)
            self._bound[binding_key] = (envelope, visitor)
            if visitor is not None:
                self._visitors[name] = visitor
        envelope, visitor = self._bound[binding_key]
        if requirement is None:
            self._resolved[(name, destination.key)] = envelope
            return envelope.value
        # The named owner explicitly shares this destination's materialization.
        # Do not grant that permission to same-location consumers of its plan.
        transferred = self._execution_transport.transfer(
            replace(envelope, repeatable_result=True), requirement,
        )
        self._resolved[(name, destination.key)] = transferred
        from mountainash.core.capabilities.policy import _CapabilityTarget

        self._coerced[(name, destination.key)] = NativeExecutionValue(
            transferred.value, envelope.location.capability_identity,
            destination.capability_identity, destination.form,
            target=_CapabilityTarget(
                destination.capability_identity,
                destination.connection if destination.connection is not None else destination.prototype,
            ),
        )
        return transferred.value

    def cache_root(self, name: str, envelope: Any, visitor: Any) -> Any:
        """Materialize one bound named result, preserving its source metadata."""
        from mountainash.conform.structured_transport import freeze_structured_field_plans
        from mountainash.core.backend_detection import native_identity
        from mountainash.core.limitations import enrich_materialization
        from mountainash.core.types import is_ibis_table, is_polars_lazyframe

        if name in self._canonical:
            return envelope
        if is_ibis_table(envelope.value):
            native = enrich_materialization(
                visitor.backend,
                lambda: materialize_native(
                    envelope.value, envelope.location.capability_identity,
                    MaterializationPurpose.DAG_CANONICAL,
                    execution_context=visitor.execution_context, scope=self._scope,
                ),
                diagnostic_trace=visitor._active_diagnostic_trace(),
                residue_checks=visitor.terminal_residue_checks(),
                execution_context=visitor.execution_context,
            )
            envelope = replace(
                envelope, value=native.value,
                source_token=self._execution_tokens.token(native.value),
                reusable_lowering=True, repeatable_result=True,
            )
        else:
            native = NativeExecutionValue(
                envelope.value, envelope.location.capability_identity,
                native_identity(envelope.value),
                ExecutionForm.LAZY if is_polars_lazyframe(envelope.value) else envelope.location.form,
                target=visitor.execution_context.target,
            )
        self._canonical[name] = CanonicalEntry(
            native, envelope.metadata.diagnostic_records,
            tuple(owned.check for owned in envelope.metadata.owned_checks),
            dict(visitor.residue_check_nodes), visitor.key_context,
            freeze_structured_field_plans(envelope.metadata.structured_field_plans),
        )
        return envelope

    def _node_for(self, name: str) -> Any:
        rel = self.dag.relations[name]
        transform = self._node_transforms.get(name)
        if transform is not None:
            rel = transform(rel)
        return rel._node

    def _destination_for(self, destination: Any) -> Any:
        if destination.connection is None:
            return destination
        return replace(
            destination,
            connection_token=self._execution_tokens.token(destination.connection),
        )

    def _canonical_node(self, name: str) -> Any:
        """Retain one transformed, connectionless source plan per named dependency."""
        if name not in self._plans:
            self._plans[name] = self._node_for(name)
        return self._plans[name]

    def _resolve_identity(
        self, name: str, *, honor_override: bool
    ) -> "tuple[CONST_BACKEND, str | None]":
        actual_family, actual_dialect = self.dag._resolve_actual_identity_for(name)
        requested = None
        if honor_override and self.target is not None:
            from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver

            requested = LocationResolver(IdentityTokens()).resolve_target(self.target)
        return _resolve_backend_and_dialect(actual_family, actual_dialect, requested)

    def _compile_named(
        self, name: str, *, honor_override: bool = False, guard_native_terminal: bool = False
    ) -> CanonicalEntry:
        """Compile and cache *name*'s canonical materialization (spec 10.2).

        A no-op re-lookup when *name* is already canonical -- the session's
        entire value proposition is that this only actually compiles once.

        *guard_native_terminal* (Task 9 step 6) raises
        :class:`~mountainash.relations.core.errors.LogicalTerminalRequired`
        immediately after compilation, before ANY native-forcing branch
        below (including an Ibis DAG_CANONICAL owned copy) -- set only
        by the single top-level call compiling a
        :meth:`RelationDAG.collect`/``collect_with_drift`` request's own
        target, never for a transitively-required dependency reached
        through this same method.
        """
        if name in self._canonical:
            return self._canonical[name]
        if name not in self.dag.relations:
            raise self.dag._unknown_ref_error(name)

        rel = self.dag.relations[name]
        transform = self._node_transforms.get(name)
        if transform is not None:
            rel = transform(rel)
        root = getattr(rel, "_node", None)
        if root is None:
            raise ValueError(f"relation {name!r} has no _node attribute")

        resolved_backend, dialect = self._resolve_identity(name, honor_override=honor_override)
        from mountainash.relations.core.execution.location import IdentityTokens
        from mountainash.relations.core.execution.metadata import MetadataSession
        from mountainash.relations.core.execution.preparation import prepare_execution
        from mountainash.relations.core.execution.transport import TransportSession
        from mountainash.relations.core.owned_copy import require_copy_idle

        prepared = prepare_execution(
            root, phase=ExecutionPhase.EXPLAIN,
            target=self.target if honor_override else None,
            identity_resolver=self._canonical_node,
        )
        placement = prepared.locations[prepared.root_key]
        from mountainash.relations.core.owned_copy import assert_prepared_owned_open
        assert_prepared_owned_open(prepared)
        require_copy_idle(placement.connection)
        if placement.family is not None:
            resolved_backend, dialect = placement.family, placement.dialect

        # Item 97: a lazy Narwhals anchor consuming a foreign-family ref
        # must reject before caching -- a cross-family transfer's eager-over-lazy
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
        from mountainash.core.capabilities.policy import (
            _identify_capability_target,
            _prepare_capability_context,
        )

        target = _identify_capability_target(
            anchor_leaf.dataframe if anchor_leaf is not None else None,
            family_override=resolved_backend,
        )
        execution_context = _prepare_capability_context(
            self._execution_policy, target, package_versions=self._package_versions,
        )
        expr_visitor = UnifiedExpressionVisitor(
            get_expression_system(resolved_backend)(
                dialect=dialect, execution_context=execution_context,
            ),
            execution_context=execution_context,
        )
        # Every dependency is key-assessed against ITS OWN constraints,
        # unconditionally -- including a no-leaf ref -- regardless of
        # whether it is the session's top-level requested name or a
        # transitively-required dependency (spec 10.5/item 48 PR-D).
        from mountainash.relations.dag.introspection import structural_schema
        key_context = KeyDriftContext(
            resource_name=name,
            constraints_for=self.dag.constraints_for,
            schema_of=lambda ref_name: structural_schema(self.dag, ref_name),
        )

        ref_resolver = _SessionRefResolver(self, execution_context)
        if self._execution_transport is None:
            self._execution_tokens = IdentityTokens()
            self._execution_metadata = MetadataSession(self._execution_tokens)
            self._execution_transport = TransportSession(self._execution_tokens)

        visitor = UnifiedRelationVisitor(
            relation_system,
            expression_visitor=expr_visitor,
            ref_resolver=ref_resolver,
            key_context=key_context,
            identity_resolver=lambda n: self.dag.relations[n]._node,
            execution_context=execution_context,
            transport=self._execution_transport,
        )

        compiled = root.accept(visitor)
        residue_checks_this = visitor.terminal_residue_checks()
        visitor.residue_checks.clear()

        root_transfer = prepared.transfers.get(prepared.root_key)
        if root_transfer is not None:
            # A retargeted native read was compiled where it lives; its recorded
            # move to the target happens before the canonical value is published.
            from mountainash.relations.core.execution.metadata import CompilationMetadata, CompiledSubtree

            compiled = self._execution_transport.transfer(
                CompiledSubtree(
                    compiled, placement, self._execution_tokens.token(root), CompilationMetadata(),
                    repeatable_result=True,
                ),
                root_transfer,
            ).value
            destination = root_transfer.destination
            resolved_backend, dialect = destination.family, destination.dialect
            execution_context = _prepare_capability_context(
                self._execution_policy,
                destination.capability_target(default_owner=compiled),
                package_versions=self._package_versions,
            )

        if guard_native_terminal:
            from mountainash.relations.core.relation_api.relation import (
                _guard_native_terminal,
            )

            _guard_native_terminal(visitor.structured_field_plans)

        from mountainash.core.backend_detection import native_identity
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
            # resource is forced eager via ONE owned copy, so every
            # later consumer within this session reuses it instead of
            # re-executing the query.
            def _thunk() -> NativeExecutionValue:
                return materialize_native(
                    compiled, compiler_identity, MaterializationPurpose.DAG_CANONICAL,
                    execution_context=execution_context, scope=self._scope,
                )

            native = enrich_materialization(
                visitor.backend, _thunk,
                diagnostic_trace=trace, residue_checks=residue_checks_this,
                execution_context=execution_context,
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
                    execution_context=execution_context, scope=self._scope,
                )

            forced = enrich_materialization(
                visitor.backend, _thunk,
                diagnostic_trace=trace, residue_checks=residue_checks_this,
                execution_context=execution_context,
            )
            if was_lazy:
                relazified = forced.value.lazy()
                native = NativeExecutionValue(
                    relazified, forced.compiler_identity,
                    native_identity(relazified),
                    ExecutionForm.LAZY, target=forced.target,
                )
            else:
                native = forced
        else:
            # No residue to enrich -- cache the raw compiled value as-is
            # (possibly still lazy), only detecting its identity.
            value_identity = native_identity(compiled)
            form = ExecutionForm.LAZY if was_lazy else ExecutionForm.EAGER
            native = NativeExecutionValue(compiled, compiler_identity, value_identity, form, target=execution_context.target)

        diagnostic_records = tuple(getattr(trace, "records", ()))

        from mountainash.conform.structured_transport import freeze_structured_field_plans

        entry = CanonicalEntry(
            native=native,
            diagnostic_records=diagnostic_records,
            residue_checks=residue_checks_this,
            residue_check_nodes=dict(visitor.residue_check_nodes),
            key_context=key_context,
            structured_field_plans=freeze_structured_field_plans(visitor.structured_field_plans),
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

    def compile_requested_native(
        self, name: str
    ) -> "tuple[NativeExecutionValue, UnifiedRelationVisitor]":
        """Compile *name* as the top-level target of a native collection
        request (:meth:`RelationDAG.collect`/``collect_with_drift``, Task 9
        step 6).

        In :attr:`SessionMode.NATIVE_COLLECTION` mode, raises
        :class:`~mountainash.relations.core.errors.LogicalTerminalRequired`
        before any native-forcing step (including an Ibis DAG_CANONICAL
        owned copy) if *name*'s own compiled plans still need a logical
        terminal -- zero ``materialize_native()`` calls for a request that
        is going to fail closed regardless. A transitively-required
        dependency reached while compiling *name* is never guarded here:
        only *name*'s own visitor is checked.
        """
        entry = self._compile_named(
            name, honor_override=True,
            guard_native_terminal=self.mode is SessionMode.NATIVE_COLLECTION,
        )
        return entry.native, self._visitors[name]

    def validation_native(
        self, name: str
    ) -> "tuple[NativeExecutionValue, UnifiedRelationVisitor]":
        """The DAG-canonical native for *name*, forced eager for validation
        (Task 6/8, spec 10.2/10.4).

        A Polars/Narwhals DAG-canonical native intentionally stays lazy so
        Polars' own optimizer can fuse shared subexpressions across
        consumers; validation needs concrete columns for identity checks
        and the logical-terminal snapshot, so this forces exactly one
        ``.collect()`` on top of the shared canonical value the first time
        *name* is validated, memoized per name so a resource validated
        more than once in the same session (e.g. a keyed identity check
        followed by a foreign-key check) shares that one collect instead
        of re-executing the query plan per call. An Ibis DAG-canonical
        native is already forced eager via an owned copy at DAG_CANONICAL
        compile time and passes through unchanged.
        """
        native, visitor = self.compile_registered(name)
        if name not in self._validation_native:
            if native.form is ExecutionForm.LAZY:
                native = materialize_native(
                    native.value, native.compiler_identity,
                    MaterializationPurpose.VALIDATION_SOURCE,
                    execution_context=visitor.execution_context, scope=self._scope,
                )
            self._validation_native[name] = native
        return self._validation_native[name], visitor

    def resolve(
        self,
        name: str,
        consumer_context: "_ExecutionContext",
    ) -> Any:
        """The raw native value for *name*, coerced to match a consumer's
        active identity if needed (spec 10.3), memoized per distinct
        ``(name, consumer_context.target.token, consumer_context.observations)``
        triple.
        A refusal only applies between *established* Ibis connection
        owners: both sides carry a bound backend (dialect
        ``ibis-<name>``) and their owner objects differ. A synthetic or
        unbound target (dialect ``None``, e.g. a join-of-refs resource
        with no own leaf, or a bare pandas dependency coerced toward an
        Ibis anchor) is not an owner and must never trigger the
        cross-connection refusal (spec 10.3).
        """
        entry = self._compile_named(name)
        native = entry.native
        src_family = native.value_identity.family
        src_dialect = native.value_identity.dialect
        if src_family is None:
            return native.value  # no-leaf ref: already anchor-family
        consumer_family = consumer_context.target.identity.family
        consumer_dialect = consumer_context.target.identity.dialect
        def _ibis_owner_dialect(target) -> "str | None":
            """Dialect only when *target* is a real bound Ibis backend."""
            identity = target.identity
            if identity.family is CONST_BACKEND.IBIS and identity.dialect is not None:
                return identity.dialect
            return None

        if (
            _ibis_owner_dialect(native.target) is not None
            and _ibis_owner_dialect(consumer_context.target) is not None
            and native.target.token != consumer_context.target.token
        ):
            raise BackendConversionError(
                "Cross-connection Ibis DAG coercion is unsupported",
                boundary_key=None,
                source_family=native.value_identity.family.value,
                source_dialect=native.value_identity.dialect,
                destination_family=consumer_family.value,
                destination_dialect=consumer_dialect,
                source_type=type(native.value).__name__,
                route="transfer_native",
                reason="no declared Ibis conversion route between distinct connection owners",
            )
        needs_coercion = src_family != consumer_family or (
            src_family is CONST_BACKEND.NARWHALS and src_dialect != consumer_dialect
        )
        if not needs_coercion:
            return native.value

        key = (name, consumer_context.target.token, consumer_context.observations)
        if key not in self._coerced:
            if self._execution_transport is None:
                from mountainash.relations.core.execution.location import IdentityTokens
                from mountainash.relations.core.execution.metadata import MetadataSession
                from mountainash.relations.core.execution.transport import TransportSession

                self._execution_tokens = IdentityTokens()
                self._execution_metadata = MetadataSession(self._execution_tokens)
                self._execution_transport = TransportSession(self._execution_tokens)
            from mountainash.relations.core.execution.location import LocationResolver

            proto = _consumer_prototype(consumer_family, consumer_dialect)
            coerced_value = self._execution_transport.transfer_native(
                native.value, LocationResolver(self._execution_tokens)._read(proto),
            )
            destination_identity = self._destination_identity(
                consumer_family, consumer_dialect
            )
            self._coerced[key] = NativeExecutionValue(
                coerced_value, native.value_identity, destination_identity, ExecutionForm.EAGER,
                target=consumer_context.target,
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
        ``MaterializationScope`` (Ibis owned-copy releases) actually
        runs: ``False`` for ordinary collection (spec 10.5 -- never
        release a value referenced by the returned native expression
        graph), ``True`` for a validation session (the sole release
        owner for its canonical native caches)."""
        if self._closed:
            return
        self._closed = True
        try:
            if self._execution_transport is not None:
                self._execution_transport.close(release_owned=release_owned)
        finally:
            if release_owned:
                self._scope.close()
