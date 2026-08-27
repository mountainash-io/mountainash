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


def coerce_to_polars(target: Any, value: Any) -> Any:
    """Coerce *value* to match a Polars *target* for cross-type join/union
    operand coercion (spec 9). Returns a lazy Polars frame -- the shape
    :class:`UnifiedRelationVisitor` expects mid-compile, unlike
    :func:`explicit_polars_egress`'s eager terminal result.

    No pandas round-trip fallback: a Narwhals value uses its own declared
    ``to_polars()``; an unrecognized value raises ``BackendConversionError``.
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

    if is_polars_lazyframe(value):
        return value
    if is_polars_dataframe(value):
        return value.lazy()
    if is_pandas_dataframe(value):
        converted = cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.PANDAS_TO_POLARS_EGRESS, pl.from_pandas, value),
        )
        return converted.lazy()
    if is_pyarrow_table(value):
        converted = cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.ARROW_TO_POLARS_EGRESS, pl.from_arrow, value),
        )
        return converted.lazy()
    if isinstance(value, dict):
        return pl.DataFrame(value).lazy()
    if isinstance(value, (list, tuple)) and (not value or isinstance(value[0], dict)):
        return pl.DataFrame(value).lazy()
    if is_ibis_table(value):
        arrow = transit_call(BoundaryKey.IBIS_TO_ARROW_EGRESS, value.to_pyarrow)
        converted = cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.ARROW_TO_POLARS_EGRESS, pl.from_arrow, arrow),
        )
        return converted.lazy()
    if is_narwhals_lazyframe(value):
        value = transit_call(BoundaryKey.NARWHALS_LAZY_COLLECT, value.collect)
    if is_narwhals_dataframe(value):
        converted = cast(
            "pl.DataFrame",
            transit_call(BoundaryKey.NARWHALS_TO_POLARS_EGRESS, value.to_polars),
        )
        return converted.lazy()

    raise BackendConversionError(
        f"Cannot coerce {type(value).__name__} to Polars for cross-type join.",
        boundary_key=None,
        source_family=None,
        source_dialect=None,
        destination_family="polars",
        destination_dialect="polars",
        source_type=type(value).__name__,
        route="coerce_to_polars",
        reason="no declared Polars conversion route for this cross-type-join operand",
    )


def coerce_to_narwhals(target: Any, value: Any) -> Any:
    """Coerce *value* to match a Narwhals *target* for cross-type join/union
    operand coercion (spec 9), then delegate exact dialect/eager-shape
    matching to :func:`coerce_narwhals_dialect`.

    A column mapping (dict) or row mapping (sequence of dicts) builds a
    destination-native Narwhals frame directly via ``nw.from_dict()``/
    ``nw.from_dicts(backend=...)`` -- never a ``pd.DataFrame()`` intermediate.
    """
    import narwhals as nw

    from mountainash.core.types import is_ibis_table, is_polars_lazyframe

    source_type = type(value).__name__
    target_namespace = nw.get_native_namespace(target)
    try:
        if isinstance(value, dict):
            converted = transit_call(
                BoundaryKey.NARWHALS_FROM_DICT_ADAPTER,
                nw.from_dict,
                value,
                backend=target_namespace,
            )
        elif isinstance(value, (list, tuple)) and (not value or isinstance(value[0], dict)):
            converted = transit_call(
                BoundaryKey.NARWHALS_FROM_DICTS_ADAPTER,
                nw.from_dicts,
                list(value),
                backend=target_namespace,
            )
        elif is_polars_lazyframe(value):
            collected = transit_call(BoundaryKey.POLARS_LAZY_COLLECT, value.collect)
            converted = nw.from_native(collected, eager_only=True)
        elif is_ibis_table(value):
            arrow = transit_call(BoundaryKey.IBIS_TO_ARROW_EGRESS, value.to_pyarrow)
            converted = nw.from_native(arrow, eager_only=True)
        else:
            converted = nw.from_native(value, eager_only=True)
    except Exception as exc:
        raise BackendConversionError(
            f"Cannot coerce {source_type} to Narwhals for cross-type join: {exc}",
            boundary_key=None,
            source_family=None,
            source_dialect=None,
            destination_family="narwhals",
            destination_dialect=None,
            source_type=source_type,
            route="coerce_to_narwhals",
            reason=str(exc),
        ) from exc
    return coerce_narwhals_dialect(target, converted)


def coerce_to_ibis(target: Any, value: Any) -> Any:
    """Coerce *value* to match an Ibis *target* for cross-type join/union
    operand coercion (spec 9).

    A column mapping (dict) or row mapping (sequence of dicts) converts to
    Arrow first (``pa.table()``/``pa.Table.from_pylist()``), then
    ``ibis.memtable()`` -- Ibis's own ``memtable()`` constructs pandas
    internally from a raw dict/list (spec 4.4's probe), so the fix routes
    through Arrow before Ibis ever sees the mapping.
    """
    from mountainash.core.types import is_narwhals_lazyframe

    source_type = type(value).__name__
    try:
        import ibis

        from mountainash.relations.backends.relation_systems.ibis._sqlite_compat import (
            ensure_sqlite_nat_adapter,
        )

        ensure_sqlite_nat_adapter()
        if isinstance(value, dict):
            import pyarrow as pa

            arrow = transit_call(BoundaryKey.ARROW_TO_IBIS_ADAPTER, ibis.memtable, pa.table(value))
            return arrow
        if isinstance(value, (list, tuple)) and (not value or isinstance(value[0], dict)):
            import pyarrow as pa

            arrow_table = pa.Table.from_pylist(list(value))
            return transit_call(BoundaryKey.ARROW_TO_IBIS_ADAPTER, ibis.memtable, arrow_table)
        if is_narwhals_lazyframe(value):
            eager = transit_call(BoundaryKey.NARWHALS_LAZY_COLLECT, value.collect)
            arrow = transit_call(BoundaryKey.NARWHALS_DIALECT_TO_ARROW, eager.to_arrow)
            return transit_call(BoundaryKey.ARROW_TO_IBIS_ADAPTER, ibis.memtable, arrow)
        return ibis.memtable(value)
    except Exception as exc:
        raise BackendConversionError(
            f"Cannot coerce {source_type} to Ibis for cross-type join: {exc}",
            boundary_key=None,
            source_family=None,
            source_dialect=None,
            destination_family="ibis",
            destination_dialect=None,
            source_type=source_type,
            route="coerce_to_ibis",
            reason=str(exc),
        ) from exc


_NW_SUPPORTED_DIALECT_IMPLEMENTATIONS = frozenset({"pandas", "polars", "pyarrow"})


def coerce_narwhals_dialect(target: Any, value: Any) -> Any:
    """Coerce *value* to match *target*'s narwhals native dialect and
    eager/lazy shape when both are narwhals frames (spec 9.1); a no-op
    otherwise, or when both already share the exact same dialect and shape.

    Each destination method is a separate, literal ``transit_call()`` site
    (never a computed ``getattr(value, method_name)``, which the closed
    census cannot verify -- spec 13.1).
    """
    from mountainash.core.backend_detection import narwhals_dialect
    from mountainash.core.types import is_narwhals_dataframe, is_narwhals_lazyframe

    if not (
        (is_narwhals_dataframe(target) or is_narwhals_lazyframe(target))
        and (is_narwhals_dataframe(value) or is_narwhals_lazyframe(value))
    ):
        return value

    target_dialect = narwhals_dialect(target)
    value_dialect = narwhals_dialect(value)
    target_is_lazy = is_narwhals_lazyframe(target)
    value_is_lazy = is_narwhals_lazyframe(value)
    if target_dialect is not None and target_dialect == value_dialect and target_is_lazy == value_is_lazy:
        return value  # identical shape: same dialect string AND same eager/lazy-ness

    if target_is_lazy:
        raise BackendConversionError(
            f"Cannot coerce a {value_dialect} operand against a lazy "
            f"{target_dialect} target for cross-dialect join/union -- "
            "narwhals does not support combining a lazy target with an "
            "eager or differently-shaped lazy operand.",
            boundary_key=None,
            source_family="narwhals",
            source_dialect=value_dialect,
            destination_family="narwhals",
            destination_dialect=target_dialect,
            source_type=type(value).__name__,
            route="coerce_narwhals_dialect",
            reason="lazy narwhals target cannot combine with an eager or differently-shaped operand",
        )

    target_implementation = target.implementation.value
    if target_implementation not in _NW_SUPPORTED_DIALECT_IMPLEMENTATIONS:
        raise BackendConversionError(
            f"Cannot coerce {value_dialect} operand to match {target_dialect} "
            "for cross-dialect join/union -- unsupported target dialect.",
            boundary_key=None,
            source_family="narwhals",
            source_dialect=value_dialect,
            destination_family="narwhals",
            destination_dialect=target_dialect,
            source_type=type(value).__name__,
            route="coerce_narwhals_dialect",
            reason=f"unsupported narwhals target implementation {target_implementation!r}",
        )

    try:
        if value_is_lazy:
            value = transit_call(BoundaryKey.NARWHALS_LAZY_COLLECT, cast(Any, value).collect)
            if narwhals_dialect(value) == target_dialect:
                return value
        import narwhals as nw

        if target_implementation == "pandas":
            converted = transit_call(BoundaryKey.NARWHALS_DIALECT_TO_PANDAS, value.to_pandas)
        elif target_implementation == "polars":
            converted = transit_call(BoundaryKey.NARWHALS_DIALECT_TO_POLARS, value.to_polars)
        else:
            converted = transit_call(BoundaryKey.NARWHALS_DIALECT_TO_ARROW, value.to_arrow)
        return nw.from_native(converted, eager_only=True)
    except Exception as exc:
        raise BackendConversionError(
            f"Failed to coerce {value_dialect} operand to {target_dialect} "
            f"for cross-dialect join/union: {exc}",
            boundary_key=None,
            source_family="narwhals",
            source_dialect=value_dialect,
            destination_family="narwhals",
            destination_dialect=target_dialect,
            source_type=type(value).__name__,
            route="coerce_narwhals_dialect",
            reason=str(exc),
        ) from exc
