"""Native execution value materializer.

Preserves native backend identity across the collection boundary: a Polars
``LazyFrame`` becomes an eager Polars ``DataFrame``, a Narwhals ``LazyFrame``
becomes an eager Narwhals ``DataFrame``, and an Ibis table stays an Ibis
table — cached only when the caller's purpose requires eager forcing (never
executed to pandas). See ``mountainash-central/04.planning/mountainash/
superpowers/specs/2026-08-27-pandas-transit-elimination-design.md`` section 7.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, cast

from mountainash.core.errors import BackendConversionError
from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.relations.core.errors import MaterializationScopeClosedError

if TYPE_CHECKING:
    from collections.abc import Callable

    import polars as pl

    from mountainash.core.capabilities.identity import BackendIdentity


class ExecutionForm(Enum):
    """How a native execution value relates to its underlying compute plan."""

    EAGER = auto()
    LAZY = auto()
    DEFERRED = auto()


class MaterializationPurpose(Enum):
    """Why a caller is materializing a compiled backend value.

    ``VALIDATION_SOURCE`` and ``DAG_CANONICAL`` are the purposes that force
    an Ibis table eager via ``.cache()`` (spec 7.2's "validation or forced
    residue" row); every other purpose passes an Ibis table through
    untouched.
    """

    NATIVE_COLLECT = auto()
    VALIDATION_SOURCE = auto()
    DAG_CANONICAL = auto()
    CONSUMER_COERCION = auto()
    DIAGNOSTIC_VIEW = auto()
    EXPLICIT_EGRESS = auto()


_IBIS_FORCE_CACHE_PURPOSES = frozenset(
    {MaterializationPurpose.VALIDATION_SOURCE, MaterializationPurpose.DAG_CANONICAL}
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
        self._releases: "list[Callable[[], None]]" = []
        self._closed = False

    def __enter__(self) -> "MaterializationScope":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def own(self, release: "Callable[[], None]") -> None:
        if self._closed:
            raise MaterializationScopeClosedError(
                "materialization scope is closed"
            )
        self._releases.append(release)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for release in reversed(self._releases):
            release()


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
    scope: "MaterializationScope | None" = None,
) -> NativeExecutionValue:
    """Force *value* into its native execution form (spec 7.2's table).

    Polars/Narwhals lazy values become eager native values via their own
    ``collect()``. An Ibis table passes through unchanged for ordinary
    collection; ``VALIDATION_SOURCE``/``DAG_CANONICAL`` purposes force it
    eager via ``.cache()`` instead — never ``.execute()``, which would
    silently convert it to pandas. Any other native value (including a
    pandas-selected source) passes through with its identity re-detected.
    """
    from mountainash.core.backend_detection import identify_backend_identity
    from mountainash.core.types import (
        is_ibis_table,
        is_narwhals_dataframe,
        is_narwhals_lazyframe,
        is_polars_dataframe,
        is_polars_lazyframe,
    )

    if is_polars_dataframe(value):
        return NativeExecutionValue(value, compiler_identity, compiler_identity, ExecutionForm.EAGER)

    if is_polars_lazyframe(value):
        polars_native = transit_call(BoundaryKey.POLARS_LAZY_COLLECT, value.collect)
        return NativeExecutionValue(polars_native, compiler_identity, compiler_identity, ExecutionForm.EAGER)

    if is_narwhals_lazyframe(value):
        narwhals_native = transit_call(BoundaryKey.NARWHALS_LAZY_COLLECT, value.collect)
        lazy_identity = identify_backend_identity(narwhals_native)
        _assert_declared_family(compiler_identity, lazy_identity)
        return NativeExecutionValue(narwhals_native, compiler_identity, lazy_identity, ExecutionForm.EAGER)

    if is_narwhals_dataframe(value):
        eager_identity = identify_backend_identity(value)
        _assert_declared_family(compiler_identity, eager_identity)
        return NativeExecutionValue(value, compiler_identity, eager_identity, ExecutionForm.EAGER)

    if is_ibis_table(value):
        if purpose in _IBIS_FORCE_CACHE_PURPOSES:
            cached = transit_call(BoundaryKey.IBIS_NATIVE_CACHE, value.cache)
            if scope is not None:
                scope.own(cached.release)
            value_identity = identify_backend_identity(cached)
            _assert_declared_family(compiler_identity, value_identity)
            return NativeExecutionValue(cached, compiler_identity, value_identity, ExecutionForm.DEFERRED)
        value_identity = identify_backend_identity(value)
        _assert_declared_family(compiler_identity, value_identity)
        return NativeExecutionValue(value, compiler_identity, value_identity, ExecutionForm.DEFERRED)

    # A pandas-selected (or otherwise unclassified) native value: preserve
    # or unwrap by caller policy upstream, retaining whatever identity is
    # actually observed (spec 7.2's "pandas source" row — a pandas family
    # here is expected, not an undeclared change).
    value_identity = identify_backend_identity(value)
    return NativeExecutionValue(value, compiler_identity, value_identity, ExecutionForm.EAGER)


def diagnostic_polars_view(native: NativeExecutionValue) -> DiagnosticFrameView:
    """Build a read-only Polars view of *native* for diagnostic/result
    transport only (spec 6.2's ``RESULT_DIAGNOSTIC_VIEW`` class).

    Never returned to execution, stored in a relation leaf, or cached in a
    DAG resolver.
    """
    import polars as pl

    from mountainash.core.types import (
        is_pandas_dataframe,
        is_polars_dataframe,
        is_polars_lazyframe,
    )

    value: Any = native.value
    if is_polars_lazyframe(value):
        value = transit_call(BoundaryKey.POLARS_LAZY_COLLECT, value.collect)
    if is_polars_dataframe(value):
        return DiagnosticFrameView(value, native.value_identity)

    if is_pandas_dataframe(value):
        pandas_frame: pl.DataFrame = pl.from_pandas(value)
        return DiagnosticFrameView(pandas_frame, native.value_identity)

    to_arrow = getattr(value, "to_pyarrow", None) or getattr(value, "to_arrow", None)
    if callable(to_arrow):
        arrow_frame = cast("pl.DataFrame", pl.from_arrow(to_arrow()))
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
    """Convert *native* to Polars via its declared route (spec 8.3).

    No non-pandas fallback: an Ibis table prefers Arrow (``to_pyarrow()``
    then ``pl.from_arrow()``), a PyArrow table converts directly, a
    pandas-selected source uses ``pl.from_pandas()``, and a Narwhals frame
    uses its own ``to_polars()``. A source with no declared route raises
    ``BackendConversionError`` instead of a silent ``to_pandas()`` detour.
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

    if is_ibis_table(value):
        arrow = transit_call(BoundaryKey.IBIS_TO_ARROW_EGRESS, value.to_pyarrow)
        return cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.ARROW_TO_POLARS_EGRESS, pl.from_arrow, arrow),
        )

    if is_pyarrow_table(value):
        return cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.ARROW_TO_POLARS_EGRESS, pl.from_arrow, value),
        )

    if is_pandas_dataframe(value):
        return cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.PANDAS_TO_POLARS_EGRESS, pl.from_pandas, value),
        )

    if is_narwhals_dataframe(value):
        return cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.NARWHALS_TO_POLARS_EGRESS, value.to_polars),
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
            return transit_call(BoundaryKey.NARWHALS_NATIVE_UNWRAP_PANDAS, value.to_native)
        return transit_call(BoundaryKey.NARWHALS_TO_PANDAS_EGRESS, value.to_pandas)

    if is_polars_dataframe(value):
        return transit_call(BoundaryKey.POLARS_TO_PANDAS_EGRESS, value.to_pandas)

    if is_ibis_table(value):
        return transit_call(BoundaryKey.IBIS_TO_PANDAS_EGRESS, value.to_pandas)

    if is_pyarrow_table(value):
        return transit_call(BoundaryKey.ARROW_TO_PANDAS_EGRESS, value.to_pandas)

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
