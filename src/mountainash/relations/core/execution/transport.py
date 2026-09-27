"""Execution-local declared operand transfers and owned resource lifetime."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from mountainash.conform.diagnostics import OperationDiagnosticTrace
from mountainash.core.capabilities.policy import (
    _CapabilityTarget, _prepare_capability_context, _resolve_policy,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.errors import BackendConversionError
from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.relations.core.errors import UnsupportedRelationTransportError
from mountainash.relations.core.materialization import (
    MaterializationScope, coerce_narwhals_dialect, coerce_to_ibis,
    coerce_to_narwhals, coerce_to_polars,
)

if TYPE_CHECKING:
    from mountainash.relations.core.execution.location import ExecutionLocation, IdentityTokens
    from mountainash.relations.core.execution.metadata import CompiledSubtree
    from mountainash.relations.core.execution.preparation import TransferRequirement


class TransportSession:
    """Cache successful transfers by compilation identity and complete destination."""

    def __init__(self, tokens: IdentityTokens, *, execution_context: Any = None,
                 context_for: Any = None) -> None:
        self.tokens = tokens
        self._cache: dict[tuple, CompiledSubtree] = {}
        self._scope = MaterializationScope()
        self._retained: list[object] = []
        self._execution_context = execution_context
        self._context_for = context_for
        self._package_versions: dict[str, str | None] = {}
        self._closed = False

    def _source_context(self, location: ExecutionLocation) -> Any:
        if self._context_for is not None:
            return self._context_for(location)
        prior = self._execution_context
        owner = location.connection if location.connection is not None else location.prototype
        if owner is None or location.capability_identity is None:
            raise RuntimeError("Cannot evaluate source residue without its execution location")
        if (prior is not None and prior.target.identity == location.capability_identity
                and prior.target.owner is owner):
            return prior
        return _prepare_capability_context(
            prior.policy if prior is not None else _resolve_policy(),
            _CapabilityTarget(location.capability_identity, owner),
            package_versions=self._package_versions,
        )

    def _source_export(self, source: CompiledSubtree, fn: Any) -> Any:
        """Evaluate source-owned checks on the exported rows before marker removal."""
        from mountainash.core.limitations import enrich_materialization
        from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

        checks = source.metadata.owned_checks
        if any(owned.source_location.key != source.location.key for owned in checks):
            raise RuntimeError("Source-owned residue must be discharged at its source boundary")
        trace = OperationDiagnosticTrace()
        trace.extend(record for record in source.metadata.diagnostic_records
                     if record.backend_family == source.location.family.value
                     and record.dialect == source.location.dialect)
        system = get_relation_system(source.location.family)()
        return enrich_materialization(
            system, fn, dialect=source.location.dialect, diagnostic_trace=trace,
            residue_checks=(owned.check for owned in checks),
            execution_context=self._source_context(source.location),
        )

    @staticmethod
    def _unsupported(source: CompiledSubtree, requirement: TransferRequirement,
                     exc: Exception | None = None) -> UnsupportedRelationTransportError:
        origin, destination = source.location, requirement.destination
        return UnsupportedRelationTransportError(
            f"No usable {requirement.route} transport from {origin.dialect} to {destination.dialect}",
            boundary_key=None,
            source_family=origin.family.value if origin.family else None,
            source_dialect=origin.dialect,
            destination_family=destination.family.value if destination.family else None,
            destination_dialect=destination.dialect,
            source_type=type(source.value).__name__, route=requirement.route,
            reason="no supported destination storage" if exc is None else type(exc).__name__,
        )

    def _convert(self, source: CompiledSubtree, requirement: TransferRequirement) -> Any:
        from mountainash.core.lazy_imports import import_ibis_expr_ops

        route = requirement.route
        value = source.value
        if route == "ibis_arrow_ibis":
            import ibis

            arrow = self._source_export(source, lambda: transit_call(
                BoundaryKey.IBIS_TO_ARROW_EGRESS, value.to_pyarrow,
            ))
            return self._import_arrow(source, requirement, ibis, arrow)
        if route == "ibis_memory_ibis":
            import ibis

            # Only a bare InMemoryTable has an eager payload. A derived
            # expression must execute at its own source, never masquerade as
            # its underlying memory leaf.
            if not isinstance(value.op(), import_ibis_expr_ops().InMemoryTable):
                return self._convert(source, replace(requirement, route="ibis_arrow_ibis"))
            arrow = self._source_export(source, lambda: value.op().data.to_pyarrow(value.schema()))
            return self._import_arrow(source, requirement, ibis, arrow)
        if route == "mapping_to_ibis":
            return self._adapt(source, requirement, coerce_to_ibis,
                               requirement.destination.prototype, self._export_checked(source))
        if route == "polars_to_ibis" or route == "narwhals_to_ibis":
            exported = self._export_checked(source)
            if route == "polars_to_ibis":
                from mountainash.core.types import is_polars_lazyframe

                if is_polars_lazyframe(exported):
                    exported = transit_call(BoundaryKey.POLARS_LAZY_COLLECT, exported.collect)
            return self._adapt(source, requirement, coerce_to_ibis,
                               requirement.destination.prototype, exported)
        if route == "ibis_to_polars" or route == "to_polars":
            return self._adapt(source, requirement, coerce_to_polars,
                               requirement.destination.prototype, self._export_checked(source))
        if route == "ibis_to_narwhals" or route == "to_narwhals":
            return self._adapt(source, requirement, coerce_to_narwhals,
                               requirement.destination.prototype, self._export_checked(source))
        if route == "narwhals_dialect":
            return self._adapt(source, requirement, coerce_narwhals_dialect,
                               requirement.destination.prototype, self._export_checked(source))
        raise self._unsupported(source, requirement)

    def _import_arrow(self, source: CompiledSubtree, requirement: TransferRequirement,
                      ibis: Any, arrow: Any) -> Any:
        try:
            return transit_call(BoundaryKey.ARROW_TO_IBIS_ADAPTER, ibis.memtable, arrow)
        except Exception as exc:
            raise self._unsupported(source, requirement, exc) from exc

    def _adapt(self, source: CompiledSubtree, requirement: TransferRequirement,
               adapter: Any, target: Any, value: Any) -> Any:
        try:
            return adapter(target, value)
        except BackendConversionError as exc:
            raise self._unsupported(source, requirement, exc) from exc

    def _export_checked(self, source: CompiledSubtree) -> Any:
        value = source.value
        if source.location.family is CONST_BACKEND.IBIS:
            return self._source_export(source, lambda: transit_call(
                BoundaryKey.IBIS_TO_ARROW_EGRESS, value.to_pyarrow,
            ))
        from mountainash.core.types import is_narwhals_lazyframe, is_polars_lazyframe

        if is_polars_lazyframe(value):
            return self._source_export(source, lambda: transit_call(
                BoundaryKey.POLARS_LAZY_COLLECT, value.collect,
            ))
        if is_narwhals_lazyframe(value):
            return self._source_export(source, lambda: transit_call(
                BoundaryKey.NARWHALS_LAZY_COLLECT, value.collect,
            ))
        if source.metadata.owned_checks or source.metadata.diagnostic_records:
            return self._source_export(source, lambda: value)
        return value

    def discharge(self, source: CompiledSubtree) -> CompiledSubtree:
        """Return the checked snapshot itself, not the original deferred plan.

        A parent may remove marker columns. In that case materialize at the
        owning source and compile the parent against precisely those checked
        rows. Retain owned Ibis caches while the returned native graph needs
        them; failed compilations release them through this session's scope.
        """
        from mountainash.core.types import is_narwhals_lazyframe, is_polars_lazyframe
        from mountainash.relations.core.execution.metadata import CompiledSubtree

        if source.location.family is CONST_BACKEND.IBIS:
            def cache():
                cached = transit_call(BoundaryKey.IBIS_NATIVE_CACHE, source.value.cache)
                self._scope.own(cached.release, owner=cached)
                self._retained.append(cached)
                return cached

            value = self._source_export(source, cache)
        else:
            deferred = is_polars_lazyframe(source.value) or is_narwhals_lazyframe(source.value)
            value = self._export_checked(source)
            if deferred and source.location.family is CONST_BACKEND.POLARS:
                from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

                value = get_relation_system(CONST_BACKEND.POLARS)().read(value)
        return CompiledSubtree(
            value, source.location, source.source_token,
            replace(source.metadata, owned_checks=()),
        )

    def transfer(self, source: CompiledSubtree, requirement: TransferRequirement) -> CompiledSubtree:
        if self._closed:
            raise RuntimeError("transport session is closed")
        key = (source.source_token, requirement.destination.key, requirement.route)
        if key in self._cache:
            return self._cache[key]
        try:
            value = self._convert(source, requirement)
            result = replace(
                source, value=value, location=requirement.destination,
                metadata=replace(source.metadata, owned_checks=()),
            )
            # Only the destination native graph (and, for an Ibis memtable,
            # its payload proxy) is proven reachable from a returned value.
            # Source caches and other metadata resources are not automatically
            # handed off; they may be released after the Arrow snapshot.
            self._retained.append(value)
            if requirement.destination.family is CONST_BACKEND.IBIS:
                self._retained.append(value.op().data)
            self._cache[key] = result
            return result
        except BaseException as primary:
            try:
                self.close(release_owned=True)
            except BaseException as cleanup:
                if hasattr(primary, "add_note"):
                    primary.add_note(f"Owned-resource cleanup also failed: {type(cleanup).__name__}")
            raise

    def __enter__(self) -> TransportSession:
        if self._closed:
            raise RuntimeError("transport session is closed")
        return self

    def __exit__(self, exc_type: Any, exc: BaseException | None, traceback: Any) -> None:
        try:
            self.close(release_owned=exc is not None)
        except BaseException as cleanup:
            if exc is None:
                raise
            if hasattr(exc, "add_note"):
                exc.add_note(f"Owned-resource cleanup also failed: {type(cleanup).__name__}")

    def close(self, *, release_owned: bool) -> None:
        if self._closed:
            return
        self._closed = True
        if not release_owned:
            # Native memtables retain their Arrow payload themselves; no
            # temporary destination tables are registered by this adapter.
            self._scope.handoff(tuple(self._retained))
        self._scope.close()
        self._cache.clear()
        self._retained.clear()
