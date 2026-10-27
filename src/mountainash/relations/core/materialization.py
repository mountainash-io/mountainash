"""Native execution value materializer.

Preserves native backend identity across the collection boundary: a Polars
``LazyFrame`` becomes an eager Polars ``DataFrame``, a Narwhals ``LazyFrame``
becomes an eager Narwhals ``DataFrame``, and an Ibis table stays an Ibis
table — copied only when the caller's purpose requires eager forcing (never
executed to pandas). See ``mountainash-central/04.planning/mountainash/
superpowers/specs/2026-08-27-pandas-transit-elimination-design.md`` section 7.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, cast

from mountainash.core.errors import BackendConversionError

from mountainash.relations.core.errors import MaterializationScopeClosedError

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    import polars as pl
    import pyarrow as pa

    from mountainash.core.capabilities.identity import BackendIdentity
    from mountainash.core.capabilities.policy import _CapabilityTarget, _ExecutionContext


class ExecutionForm(Enum):
    """How a native execution value relates to its underlying compute plan."""

    EAGER = auto()
    LAZY = auto()
    DEFERRED = auto()


class MaterializationPurpose(Enum):
    """Why a caller is materializing a compiled backend value.

    ``VALIDATION_SOURCE`` and ``DAG_CANONICAL`` are the purposes that force
    an Ibis table eager via an owned copy (spec 7.2's "validation or forced
    residue" row); every other purpose passes an Ibis table through
    untouched.
    """

    NATIVE_COLLECT = auto()
    VALIDATION_SOURCE = auto()
    DAG_CANONICAL = auto()
    LOGICAL_TERMINAL = auto()
    CONSUMER_COERCION = auto()
    DIAGNOSTIC_VIEW = auto()
    EXPLICIT_EGRESS = auto()


_IBIS_FORCE_COPY_PURPOSES = frozenset(
    {
        MaterializationPurpose.VALIDATION_SOURCE,
        MaterializationPurpose.DAG_CANONICAL,
        MaterializationPurpose.LOGICAL_TERMINAL,
    }
)


@dataclass(frozen=True)
class NativeExecutionValue:
    """One materialized backend-native value and its identity provenance.

    ``compiler_identity`` names the backend that compiled the value.
    ``value_identity`` names the observed native value after allowed
    materialization. The two normally match; only a declared adapter can
    change ``value_identity``.
    """

    value: Any
    compiler_identity: "BackendIdentity"
    value_identity: "BackendIdentity"
    form: ExecutionForm
    target: "_CapabilityTarget"


@dataclass(frozen=True)
class DiagnosticFrameView:
    """A read-only Polars view for result transport only.

    Never a canonical execution value, never stored in a relation leaf or a
    DAG resolver cache (spec 6.2/6.3).
    """

    frame: "pl.DataFrame"
    source_identity: "BackendIdentity"


class MaterializationScope:
    """Owns the native caches created during one materialization.

    Release callbacks run once, in reverse creation order. Only caches this
    scope itself created are released — no scope releases another scope's
    cache (spec 7.3).
    """

    def __init__(self) -> None:
        self._releases: "list[tuple[object | None, Callable[[], None]]]" = []
        self._closed = False

    def __enter__(self) -> "MaterializationScope":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        try:
            self.close()
        except BaseException as cleanup:
            if exc_value is None:
                raise
            if hasattr(exc_value, "add_note"):
                exc_value.add_note(
                    f"Owned-resource cleanup also failed: {type(cleanup).__name__}"
                )

    def own(self, release: "Callable[[], None]", *, owner: object | None = None) -> None:
        if self._closed:
            raise MaterializationScopeClosedError(
                "materialization scope is closed"
            )
        self._releases.append((owner, release))

    def handoff(self, owners: "tuple[object, ...]") -> None:
        """Detach only dependencies explicitly proven reachable from a native result."""
        if self._closed:
            raise MaterializationScopeClosedError("materialization scope is closed")
        self._releases = [
            (owner, release) for owner, release in self._releases
            if not any(owner is retained for retained in owners)
        ]

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        errors: list[BaseException] = []
        for _, release in reversed(self._releases):
            try:
                release()
            except BaseException as exc:
                errors.append(exc)
        self._releases.clear()
        if errors:
            first = errors[0]
            if hasattr(first, "add_note"):
                for extra in errors[1:]:
                    first.add_note(f"Additional owned-resource cleanup failed: {type(extra).__name__}")
            raise first


def rows_to_arrow(rows: Sequence[Mapping[str, Any]]) -> "pa.Table":
    """Arrow table from row dicts with every key any row carries (first-seen order).

    ``pa.Table.from_pylist`` takes its columns from the first row only and
    silently drops keys that first appear later; here a key missing from a
    row becomes null, matching Polars and Narwhals row ingress.
    """
    import pyarrow as pa

    names = list(dict.fromkeys(name for row in rows for name in row))
    return pa.table({name: [row.get(name) for row in rows] for name in names})


def _assert_declared_family(
    compiler_identity: "BackendIdentity", value_identity: "BackendIdentity"
) -> None:
    """Raise unless *value_identity* preserves *compiler_identity*'s family.

    Only a declared adapter (a separate, explicitly-classified boundary) may
    change the observed family; materialization itself never does.
    """
    if compiler_identity.family != value_identity.family:
        raise BackendConversionError(
            "materialize_native() observed an undeclared backend family "
            "change during native forcing",
            boundary_key=None,
            source_family=str(compiler_identity.family),
            source_dialect=compiler_identity.dialect,
            destination_family=str(value_identity.family),
            destination_dialect=value_identity.dialect,
            source_type=type(compiler_identity).__name__,
            route="native_materialization",
            reason=(
                "materialize_native() must preserve the compiler identity's "
                "backend family; only a declared adapter may change it"
            ),
        )


def materialize_native(
    value: Any,
    compiler_identity: "BackendIdentity",
    purpose: MaterializationPurpose,
    *,
    execution_context: "_ExecutionContext",
    scope: "MaterializationScope | None" = None,
) -> NativeExecutionValue:
    """Force *value* into its native execution form (spec 7.2's table).

    Polars/Narwhals lazy values become eager native values via their own
    ``collect()``. An Ibis table passes through unchanged for ordinary
    collection; ``VALIDATION_SOURCE``/``DAG_CANONICAL`` purposes force it
    eager via an owned copy instead — never ``.execute()``, which would
    silently convert it to pandas. Any other native value (including a
    pandas-selected source) passes through with its identity re-detected.

    ``execution_context.target`` becomes every resulting carrier's own
    ``target`` -- the actual native owner this value was produced for.
    """
    from mountainash.core.backend_detection import native_identity
    from mountainash.core.types import (
        is_ibis_table,
        is_narwhals_dataframe,
        is_narwhals_lazyframe,
        is_polars_dataframe,
        is_polars_lazyframe,
    )

    target = execution_context.target

    if is_polars_dataframe(value):
        return NativeExecutionValue(value, compiler_identity, compiler_identity, ExecutionForm.EAGER, target=target)

    if is_polars_lazyframe(value):
        polars_native = value.collect()
        return NativeExecutionValue(polars_native, compiler_identity, compiler_identity, ExecutionForm.EAGER, target=target)

    if is_narwhals_lazyframe(value):
        narwhals_native = value.collect()
        lazy_identity = native_identity(narwhals_native)
        _assert_declared_family(compiler_identity, lazy_identity)
        return NativeExecutionValue(narwhals_native, compiler_identity, lazy_identity, ExecutionForm.EAGER, target=target)

    if is_narwhals_dataframe(value):
        eager_identity = native_identity(value)
        _assert_declared_family(compiler_identity, eager_identity)
        return NativeExecutionValue(value, compiler_identity, eager_identity, ExecutionForm.EAGER, target=target)

    if is_ibis_table(value):
        if purpose in _IBIS_FORCE_COPY_PURPOSES:
            from mountainash.relations.core.owned_copy import owned_ibis_table

            copy = owned_ibis_table(value)
            if scope is not None and copy.release is not None:
                scope.own(copy.release, owner=copy.value)
            value_identity = native_identity(copy.value)
            _assert_declared_family(compiler_identity, value_identity)
            return NativeExecutionValue(copy.value, compiler_identity, value_identity, ExecutionForm.DEFERRED, target=target)
        value_identity = native_identity(value)
        _assert_declared_family(compiler_identity, value_identity)
        return NativeExecutionValue(value, compiler_identity, value_identity, ExecutionForm.DEFERRED, target=target)

    # A pandas-selected (or otherwise unclassified) native value: preserve
    # or unwrap by caller policy upstream, retaining whatever identity is
    # actually observed (spec 7.2's "pandas source" row — a pandas family
    # here is expected, not an undeclared change).
    value_identity = native_identity(value)
    return NativeExecutionValue(value, compiler_identity, value_identity, ExecutionForm.EAGER, target=target)


def diagnostic_polars_view(native: NativeExecutionValue) -> DiagnosticFrameView:
    """Build a read-only Polars view of *native* for diagnostic/result
    transport only (spec 6.2's ``RESULT_DIAGNOSTIC_VIEW`` class).

    Never returned to execution, stored in a relation leaf, or cached in a
    DAG resolver.
    """
    import polars as pl

    from mountainash.core.types import (
        is_ibis_table,
        is_narwhals_dataframe,
        is_narwhals_lazyframe,
        is_pandas_dataframe,
        is_polars_dataframe,
        is_polars_lazyframe,
        is_pyarrow_table,
    )

    value: Any = native.value
    if is_narwhals_lazyframe(value):
        value = value.collect()
    if is_polars_lazyframe(value):
        value = value.collect()
    if is_polars_dataframe(value):
        return DiagnosticFrameView(value, native.value_identity)

    if is_pandas_dataframe(value):
        pandas_frame: pl.DataFrame = pl.from_pandas(value)
        return DiagnosticFrameView(pandas_frame, native.value_identity)

    if is_ibis_table(value):
        arrow_native = value.to_pyarrow()
        arrow_frame = cast("pl.DataFrame", pl.from_arrow(arrow_native))
        return DiagnosticFrameView(arrow_frame, native.value_identity)

    if is_pyarrow_table(value):
        arrow_frame = cast("pl.DataFrame", pl.from_arrow(value))
        return DiagnosticFrameView(arrow_frame, native.value_identity)

    if is_narwhals_dataframe(value):
        arrow_native = value.to_arrow()
        arrow_frame = cast("pl.DataFrame", pl.from_arrow(arrow_native))
        return DiagnosticFrameView(arrow_frame, native.value_identity)

    raise BackendConversionError(
        "diagnostic_polars_view() has no declared conversion route for this "
        "native value",
        boundary_key=None,
        source_family=str(native.value_identity.family),
        source_dialect=native.value_identity.dialect,
        destination_family="polars",
        destination_dialect="polars",
        source_type=type(value).__name__,
        route="diagnostic_polars_view",
        reason=(
            "no declared Polars, Arrow, or pandas conversion route for this "
            "native type"
        ),
    )


def explicit_polars_egress(native: NativeExecutionValue) -> "pl.DataFrame":
    """Convert a recognized native value to an eager Polars frame.

    Polars imports pandas, Arrow and Ibis values through its native
    constructor. Narwhals retains its own terminal to preserve native
    index and object semantics. Unsupported inputs raise BackendConversionError.
    """
    import polars as pl

    from mountainash.core.types import (
        is_ibis_table,
        is_narwhals_dataframe,
        is_pandas_dataframe,
        is_polars_dataframe,
        is_pyarrow_table,
    )

    value = native.value

    if is_polars_dataframe(value):
        return value

    if is_ibis_table(value) or is_pyarrow_table(value) or is_pandas_dataframe(value):
        return pl.DataFrame(value)

    if is_narwhals_dataframe(value):
        return cast(
            "pl.DataFrame",
            value.to_polars(),
        )

    raise BackendConversionError(
        "explicit_polars_egress() has no declared conversion route for this "
        "native value",
        boundary_key=None,
        source_family=str(native.value_identity.family),
        source_dialect=native.value_identity.dialect,
        destination_family="polars",
        destination_dialect="polars",
        source_type=type(value).__name__,
        route="explicit_polars_egress",
        reason="no declared Polars conversion route for this native type",
    )


def explicit_pandas_egress(native: NativeExecutionValue) -> Any:
    """Convert *native* to pandas via its declared route (spec 8.3).

    A pandas-selected source passes through (or unwraps from Narwhals). Every
    other family calls its own native ``to_pandas()`` terminal directly --
    Ibis and PyArrow never route through ``explicit_polars_egress()`` first.
    """
    from mountainash.core.types import (
        is_ibis_table,
        is_narwhals_dataframe,
        is_pandas_dataframe,
        is_polars_dataframe,
        is_pyarrow_table,
    )

    value = native.value

    if is_pandas_dataframe(value):
        return value

    if is_narwhals_dataframe(value):
        if native.value_identity.dialect == "narwhals-pandas":
            return value.to_native()
        return value.to_pandas()

    if is_polars_dataframe(value):
        return value.to_pandas()

    if is_ibis_table(value):
        return value.to_pandas()

    if is_pyarrow_table(value):
        return value.to_pandas()

    raise BackendConversionError(
        "explicit_pandas_egress() has no declared conversion route for this "
        "native value",
        boundary_key=None,
        source_family=str(native.value_identity.family),
        source_dialect=native.value_identity.dialect,
        destination_family="pandas",
        destination_dialect="pandas",
        source_type=type(value).__name__,
        route="explicit_pandas_egress",
        reason="no declared pandas conversion route for this native type",
    )
