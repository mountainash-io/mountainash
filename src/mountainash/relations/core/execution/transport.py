"""Execution-local declared operand transfers and owned resource lifetime."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from mountainash.conform.diagnostics import OperationDiagnosticTrace
from mountainash.core.capabilities.policy import (
    _prepare_capability_context, _resolve_policy,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.errors import BackendConversionError

from mountainash.relations.core.errors import UnsupportedRelationTransportError
from mountainash.relations.core.execution.location import ExecutionLocation, LocationResolver
from mountainash.relations.core.execution.metadata import CompilationMetadata, CompiledSubtree, Imported
from mountainash.relations.core.materialization import ExecutionForm, MaterializationScope, rows_to_arrow
from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

if TYPE_CHECKING:
    from mountainash.relations.core.execution.location import IdentityTokens
    from mountainash.relations.core.execution.preparation import TransferRequirement


def import_refusal(
    source: ExecutionLocation, destination: ExecutionLocation, cause: BaseException | None,
) -> UnsupportedRelationTransportError:
    """The one owner of import-refusal enrichment for a source -> destination boundary."""
    def label(location: ExecutionLocation) -> str:
        return location.dialect or (location.family.value if location.family else "unknown")

    if cause is None:
        reason = "no declared adapter"
        message = f"No declared transport from {label(source)} to {label(destination)}"
    else:
        reason = type(cause).__name__
        message = f"No usable transport from {label(source)} to {label(destination)}"
    return UnsupportedRelationTransportError(
        message, boundary_key=None,
        source_family=source.family.value if source.family else None,
        source_dialect=source.dialect,
        destination_family=destination.family.value if destination.family else None,
        destination_dialect=destination.dialect,
        source_type="RelationNode", route="import_into", reason=reason,
    )


def _is_raw(value: Any) -> bool:
    return isinstance(value, dict) or (
        isinstance(value, (list, tuple)) and (not value or isinstance(value[0], dict))
    )


def _implementation(location: ExecutionLocation) -> str | None:
    """The native library a location's values live in, whatever wraps them."""
    if location.family is CONST_BACKEND.POLARS:
        return "polars"
    if location.family is CONST_BACKEND.NARWHALS and location.dialect:
        name = location.dialect.removeprefix("narwhals-")
        return "polars" if name == "lazy" else name
    return None


def _same_implementation(a: ExecutionLocation, b: ExecutionLocation) -> bool:
    """Both sides hold one native implementation: only wrapping and form can differ."""
    implementation = _implementation(a)
    return implementation is not None and implementation == _implementation(b)


def _native_move(value: Any, destination: ExecutionLocation) -> Any:
    """Unwrap/wrap and change eager/lazy form without leaving the native library."""
    import narwhals as nw

    wrapped = isinstance(value, (nw.DataFrame, nw.LazyFrame))
    if destination.family is CONST_BACKEND.POLARS:
        value = value.to_native() if wrapped else value
    elif not wrapped:
        value = nw.from_native(value)
    deferred = hasattr(value, "collect")
    if destination.form is ExecutionForm.LAZY:
        return value if deferred else value.lazy()
    return value.collect() if deferred else value


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
        target = location.capability_target()
        if target is None:
            raise RuntimeError("Cannot evaluate source residue without its execution location")
        if (prior is not None and prior.target.identity == target.identity
                and prior.target.owner is target.owner):
            return prior
        return _prepare_capability_context(
            prior.policy if prior is not None else _resolve_policy(),
            target, package_versions=self._package_versions,
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

    def _export(self, source: CompiledSubtree) -> pa.Table:
        """Destination-blind Arrow export, with source-owned residue checks applied."""
        system = get_relation_system(source.location.family)()

        def export() -> pa.Table:
            return system.export(source.value, source=source.location)

        if source.metadata.owned_checks or source.metadata.diagnostic_records:
            return self._source_export(source, export)
        return export()

    def discharge(self, source: CompiledSubtree) -> CompiledSubtree:
        """Return the checked snapshot itself, not the original deferred plan.

        A parent may remove marker columns. In that case materialize at the
        owning source and compile the parent against precisely those checked
        rows. Retain owned Ibis caches while the returned native graph needs
        them; failed compilations release them through this session's scope.
        """
        if not source.repeatable_result:
            source = replace(
                source, source_token=self.tokens.token(object()), reusable_lowering=False,
            )
        if source.location.family is CONST_BACKEND.IBIS:
            from mountainash.relations.core.owned_copy import owned_ibis_table

            def copy_source():
                copy = owned_ibis_table(source.value)
                if copy.release is not None:
                    self._scope.own(copy.release, owner=copy.value)
                self._retained.append(copy.value)
                return copy.value

            value = self._source_export(source, copy_source)
        else:
            system = get_relation_system(source.location.family)()
            value = system.import_into(self._source_export(
                source, lambda: system.export(source.value, source=source.location),
            ), location=source.location).value
            if source.location.family is CONST_BACKEND.POLARS:
                value = system.read(value)
        return replace(
            source, value=value, metadata=replace(source.metadata, owned_checks=()),
        )

    def transfer(self, source: CompiledSubtree, requirement: TransferRequirement) -> CompiledSubtree:
        if self._closed:
            raise RuntimeError("transport session is closed")
        if not source.repeatable_result:
            source = replace(
                source, source_token=self.tokens.token(object()), reusable_lowering=False,
            )
        destination = requirement.destination
        key = (source.source_token, destination.key, requirement.owned)
        if key in self._cache:
            return self._cache[key]
        try:
            imported = self._move(source, requirement)
            result = replace(
                source, value=imported.value, location=destination,
                metadata=replace(source.metadata, owned_checks=()),
            )
            self._retain(imported, destination)
            self._cache[key] = result
            return result
        except BaseException as primary:
            try:
                self.close(release_owned=True)
            except BaseException as cleanup:
                if hasattr(primary, "add_note"):
                    primary.add_note(f"Owned-resource cleanup also failed: {type(cleanup).__name__}")
            raise

    def _physically_bound(self, source: CompiledSubtree) -> bool:
        """Whether the value itself, not merely its prepared label, lives on a connection."""
        return LocationResolver(self.tokens)._read(source.value).binding == "bound"

    def _move(self, source: CompiledSubtree, requirement: TransferRequirement) -> Imported:
        src, destination, value = source.location, requirement.destination, source.value
        if _is_raw(value):
            arrow = rows_to_arrow(list(value)) if isinstance(value, (list, tuple)) else pa.table(value)
        elif not requirement.owned and src.key == destination.key and self._physically_bound(source):
            return Imported(value)
        elif not requirement.owned and _same_implementation(src, destination):
            return Imported(_native_move(value, destination))
        else:
            arrow = self._export(source)
        try:
            return get_relation_system(destination.family)().import_into(
                arrow, location=destination, owned=requirement.owned,
            )
        except (BackendConversionError, ValueError) as exc:
            raise import_refusal(src, destination, exc) from exc

    def _retain(self, imported: Imported, destination: ExecutionLocation) -> None:
        """Keep the destination graph alive and register the lifetime of what it created."""
        self._retained.append(imported.value)
        if destination.family is not CONST_BACKEND.IBIS:
            return
        from ibis.expr import operations as ops

        op = imported.value.op()
        self._retained.append(op)
        if imported.release is not None:
            self._scope.own(imported.release, owner=op)
        if not isinstance(op, ops.InMemoryTable):
            return
        # Only the memtable's payload proxy is proven reachable from a returned value.
        self._retained.append(op.data)
        connection = destination.connection
        if connection is None:
            return

        def release_import():
            # Ibis retains registered memtables for the connection's
            # lifetime. This payload is ours, not the caller's.
            if op not in connection._memtables:
                return
            if connection.name == "duckdb":
                connection.con.unregister(op.name)
            elif connection.name == "polars":
                connection.drop_table(op.name, force=True)
            else:
                from mountainash.relations.backends.relation_systems.ibis._physical import (
                    adopt_connection, owned_transaction,
                )
                with adopt_connection(connection) as backend:
                    with owned_transaction(backend):
                        backend.drop_table(op.name, force=True)
            connection._memtables.discard(op)

        self._scope.own(release_import, owner=op.data)

    def transfer_native(self, value: Any, destination: ExecutionLocation) -> Any:
        """Unowned wrapper for exactly two legacy callers: the unprepared DAG-validation visitor and
        ``DAGMaterializationSession.resolve``. Deleted when item 249 moves them onto prepared execution."""
        from mountainash.relations.core.execution.preparation import TransferRequirement

        if _is_raw(value):
            source = ExecutionLocation(CONST_BACKEND.POLARS, "polars", ExecutionForm.EAGER, "bound")
        else:
            source = LocationResolver(self.tokens)._read(value)
        subtree = CompiledSubtree(value, source, self.tokens.token(value), CompilationMetadata())
        return self.transfer(subtree, TransferRequirement("native", destination, False)).value

    def validate(self, source: CompiledSubtree, destination: ExecutionLocation) -> None:
        """Compile-phase storage check for a bare-memory payload; nothing is imported."""
        try:
            get_relation_system(destination.family)().check_import(
                get_relation_system(source.location.family)().export(source.value, source=source.location),
                location=destination,
            )
        except ValueError as exc:
            raise import_refusal(source.location, destination, exc) from exc

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
        try:
            self._scope.close()
        finally:
            self._cache.clear()
            self._retained.clear()
