"""One physical snapshot and deterministic logical structured resolution."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol, cast

from mountainash.conform.errors import ConformTransformError
from mountainash.conform.structured_transport import (
    INVALID_STRUCTURED_VALUE,
    StructuredActionConsumer,
    StructuredFieldPlanMap,
    resolve_structured_cell,
    transport_arrow_dtype,
)
from mountainash.core.constants import CONST_BACKEND


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    import pandas as pd
    import polars as pl
    import pyarrow as pa

    from mountainash.core.capabilities.identity import BackendIdentity


@dataclass(frozen=True)
class LogicalTerminalSnapshot:
    """One eager physical read shared by all logical structured consumers."""

    columns: Mapping[str, Sequence[Any]]
    row_ordinals: tuple[int, ...]
    source_identity: BackendIdentity


@dataclass(frozen=True)
class ResolvedLogicalSnapshot:
    """Logical transported values and the physical rows retained for output."""

    physical: LogicalTerminalSnapshot
    logical_columns: Mapping[str, Sequence[Any]]
    keep_ordinals: tuple[int, ...]
    target_dtypes: Mapping[str, Any]


class LogicalSnapshotAdapter(Protocol):
    """Backend-owned eager extraction boundary for one physical native carrier."""

    family: CONST_BACKEND

    def snapshot(self, native: Any) -> LogicalTerminalSnapshot: ...

    def to_polars(self, resolved: ResolvedLogicalSnapshot) -> "pl.DataFrame": ...

    def to_pandas(self, resolved: ResolvedLogicalSnapshot) -> Any: ...


def _snapshot_from_columns(native: Any, columns: dict[str, Sequence[Any]]) -> LogicalTerminalSnapshot:
    row_count = len(next(iter(columns.values()))) if columns else 0
    return LogicalTerminalSnapshot(
        columns=MappingProxyType(columns),
        row_ordinals=tuple(range(row_count)),
        source_identity=native.value_identity,
    )


def _keep_positions(resolved: ResolvedLogicalSnapshot) -> list[int]:
    """Positions of ``keep_ordinals`` within the physical snapshot's own row
    ordinals -- never assumes ordinals are already 0-based positions."""
    index_of = {ordinal: position for position, ordinal in enumerate(resolved.physical.row_ordinals)}
    return [index_of[ordinal] for ordinal in resolved.keep_ordinals]


def _slice_native(family: CONST_BACKEND, column: Any, positions: list[int]) -> Any:
    """Select rows by position from one native untagged column, preserving
    its dtype and without re-executing the source (spec Task 4 step 6)."""
    if family is CONST_BACKEND.PANDAS:
        return column.iloc[positions]
    if family is CONST_BACKEND.POLARS:
        return column[positions]
    # PyArrow, Narwhals, and Ibis snapshots all capture PyArrow-native
    # columns (see the adapters below); ChunkedArray/Array both expose
    # take(). An empty Python list has no elements to infer a type from,
    # so PyArrow would otherwise build a null-typed indices array and
    # reject the kernel lookup against the real column dtype -- force
    # int64 explicitly so the empty-input (vacuous pass) case works for
    # every column dtype, not just the ones PyArrow happens to infer.
    import pyarrow as pa

    return column.take(pa.array(positions, type=pa.int64()))


def _transported_array(values: Any, dtype: Any) -> Any:
    import pyarrow as pa
    import pyarrow.compute as pc

    return pa.array([
        pc.cast(value, dtype) if isinstance(value, pa.Scalar) and value.type != dtype else value
        for value in values
    ], type=dtype)


def _materialize_transported_polars(name: str, values: Any, dtype: Any) -> Any:
    """Preserve validated physical values across logical egress."""
    import polars as pl

    if dtype is None:
        return pl.Series(name, values, dtype=pl.Object)
    return pl.from_arrow(_transported_array(values, dtype)).rename(name)


def _materialize_transported_pandas(name: str, values: Any, dtype: Any) -> Any:
    """Keep the same validated Arrow type and values at pandas egress."""
    import pandas as pd

    if dtype is None:
        return pd.Series(values, name=name, dtype=object)
    return pd.Series(_transported_array(values, dtype), name=name, dtype=pd.ArrowDtype(dtype))


class _BaseSnapshotAdapter:
    """Shared output reconstruction for one native family's captured columns."""

    family: CONST_BACKEND

    def _output_columns(
        self, resolved: ResolvedLogicalSnapshot
    ) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
        positions = _keep_positions(resolved)
        names = list(resolved.physical.columns)
        transported: dict[str, Any] = {}
        untagged: dict[str, Any] = {}
        for name in names:
            physical = resolved.physical.columns[name]
            logical = resolved.logical_columns[name]
            if logical is physical:
                untagged[name] = _slice_native(self.family, physical, positions)
            else:
                transported[name] = logical
        return names, transported, untagged

    def to_polars(self, resolved: ResolvedLogicalSnapshot) -> "pl.DataFrame":
        import polars as pl

        names, transported, untagged = self._output_columns(resolved)
        columns: dict[str, Any] = {}
        for name in names:
            if name in transported:
                columns[name] = _materialize_transported_polars(
                    name, transported[name], resolved.target_dtypes.get(name)
                )
            else:
                columns[name] = _native_column_to_polars(self.family, untagged[name])
        return pl.DataFrame(columns)

    def to_pandas(self, resolved: ResolvedLogicalSnapshot) -> Any:
        import pandas as pd

        names, transported, untagged = self._output_columns(resolved)
        columns: dict[str, Any] = {}
        for name in names:
            if name in transported:
                columns[name] = _materialize_transported_pandas(
                    name, transported[name], resolved.target_dtypes.get(name)
                )
            else:
                columns[name] = _native_column_to_pandas(self.family, untagged[name])
        return pd.DataFrame(columns)


def _native_column_to_polars(family: CONST_BACKEND, column: Any) -> "pl.Series":
    import polars as pl

    if family is CONST_BACKEND.POLARS:
        return cast("pl.Series", column)
    if family is CONST_BACKEND.PANDAS:
        return cast(
            "pl.Series",
            pl.from_pandas(column),
        )
    return cast(
        "pl.Series",
        pl.from_arrow(column),
    )


def _native_column_to_pandas(family: CONST_BACKEND, column: Any) -> "pd.Series":
    if family is CONST_BACKEND.PANDAS:
        return cast("pd.Series", column)
    if family is CONST_BACKEND.POLARS:
        return cast(
            "pd.Series",
            column.to_pandas(),
        )
    return cast(
        "pd.Series",
        column.to_pandas(),
    )


class _PolarsSnapshotAdapter(_BaseSnapshotAdapter):
    family = CONST_BACKEND.POLARS

    def snapshot(self, native: Any) -> LogicalTerminalSnapshot:
        frame = native.value
        return _snapshot_from_columns(
            native, {name: frame.get_column(name) for name in frame.columns}
        )


class _PandasSnapshotAdapter(_BaseSnapshotAdapter):
    family = CONST_BACKEND.PANDAS

    def snapshot(self, native: Any) -> LogicalTerminalSnapshot:
        frame = native.value
        return _snapshot_from_columns(native, {name: frame[name] for name in frame.columns})


class _PyArrowSnapshotAdapter(_BaseSnapshotAdapter):
    family = CONST_BACKEND.PYARROW

    def snapshot(self, native: Any) -> LogicalTerminalSnapshot:
        table = native.value
        return _snapshot_from_columns(
            native, {name: table.column(name) for name in table.column_names}
        )


class _NarwhalsSnapshotAdapter(_BaseSnapshotAdapter):
    family = CONST_BACKEND.NARWHALS

    def snapshot(self, native: Any) -> LogicalTerminalSnapshot:
        arrow = native.value.to_arrow()
        return _snapshot_from_columns(
            native, {name: arrow.column(name) for name in arrow.column_names}
        )


class _IbisSnapshotAdapter(_BaseSnapshotAdapter):
    family = CONST_BACKEND.IBIS

    def snapshot(self, native: Any) -> LogicalTerminalSnapshot:
        arrow = native.value.to_pyarrow()
        return _snapshot_from_columns(
            native, {name: arrow.column(name) for name in arrow.column_names}
        )


_ADAPTERS: tuple[LogicalSnapshotAdapter, ...] = (
    _PolarsSnapshotAdapter(),
    _PandasSnapshotAdapter(),
    _PyArrowSnapshotAdapter(),
    _NarwhalsSnapshotAdapter(),
    _IbisSnapshotAdapter(),
)
LOGICAL_SNAPSHOT_ADAPTERS: Mapping[CONST_BACKEND, LogicalSnapshotAdapter] = MappingProxyType(
    {adapter.family: adapter for adapter in _ADAPTERS}
)


def _resolution_error(field_name: str, plan: Any, row_ordinal: int) -> ConformTransformError:
    return ConformTransformError.structured(
        field_name=field_name,
        expected_root=plan.root.value,
        row_ordinal=row_ordinal,
    )


def _python_value(value: Any) -> Any:
    """Normalize a backend cell before structured resolution.

    Arrow scalar wrappers use ``as_py()``; native Polars array cells use
    ``to_list()``. The latter copies contents, costing time and memory
    proportional to the converted values during the existing logical-value
    traversal. It is not zero-copy, schema inference, or another source execution.
    """
    import polars as pl

    if isinstance(value, pl.Series):
        return value.to_list()
    as_py = getattr(value, "as_py", None)
    return as_py() if callable(as_py) else value


def resolve_logical_snapshot(
    snapshot: LogicalTerminalSnapshot,
    plans: StructuredFieldPlanMap,
    *,
    consumer: StructuredActionConsumer = StructuredActionConsumer.LOGICAL_EGRESS,
) -> ResolvedLogicalSnapshot:
    """Decode every transported cell once and combine discard-row masks."""
    row_count = len(snapshot.row_ordinals)
    if any(len(column) != row_count for column in snapshot.columns.values()):
        raise ValueError("logical snapshot columns must share the ordinal length")

    import pyarrow as pa
    from mountainash.core.dtypes import MountainashDtype, SchemaTypeStatus, dtype_is_complete

    native_dtypes = {}
    resolved_transport: dict[str, tuple[Any, ...]] = {}
    keep = [True] * row_count
    for field_name, plan in plans.items():
        physical = snapshot.columns.get(field_name)
        if physical is None:
            continue
        typed = (
            consumer is StructuredActionConsumer.LOGICAL_EGRESS
            and plan.requires_logical_terminal
            and plan.target_dtype is not None
            and plan.target_dtype is not SchemaTypeStatus.UNKNOWN
            and plan.target_dtype not in (MountainashDtype.LIST, MountainashDtype.STRUCT)
        )
        complete = typed and dtype_is_complete(plan.target_dtype)
        native_dtype = transport_arrow_dtype(plan.target_dtype) if complete else None
        values: list[Any] = []
        for index, value in enumerate(physical):
            resolution = resolve_structured_cell(
                _python_value(value), plan=plan, consumer=consumer, native_dtype=native_dtype,
            )
            if (
                resolution.logical_value is INVALID_STRUCTURED_VALUE
                and plan.configured_action == "coerce"
                and consumer is StructuredActionConsumer.LOGICAL_EGRESS
            ):
                # Spec 12.3: a logical egress raises for an invalid `coerce`
                # value; validation reports the same invalid source through
                # TYPE_FORMAT instead of raising out of check execution.
                raise _resolution_error(field_name, plan, snapshot.row_ordinals[index])
            values.append(resolution.logical_value)
            keep[index] = keep[index] and resolution.keep
        resolved_transport[field_name] = tuple(values)
        if complete:
            native_dtypes[field_name] = native_dtype
        elif typed:
            types = {value.type for value in values if isinstance(value, pa.Scalar)}
            if types:
                native_dtypes[field_name] = pa.unify_schemas(
                    [pa.schema([(field_name, dtype)]) for dtype in types],
                    promote_options="permissive",
                ).field(field_name).type
            else:
                native_dtypes[field_name] = transport_arrow_dtype(plan.target_dtype)

    retained_indexes = tuple(index for index, row_keep in enumerate(keep) if row_keep)
    logical_columns: dict[str, Sequence[Any]] = {
        name: tuple(values[index] for index in retained_indexes)
        for name, values in resolved_transport.items()
    }
    for name, physical in snapshot.columns.items():
        logical_columns.setdefault(name, physical)
    return ResolvedLogicalSnapshot(
        physical=snapshot,
        logical_columns=MappingProxyType(logical_columns),
        keep_ordinals=tuple(snapshot.row_ordinals[index] for index in retained_indexes),
        target_dtypes=MappingProxyType(native_dtypes),
    )


def logical_terminal_snapshot(native: Any) -> LogicalTerminalSnapshot:
    """Extract one eager logical-terminal snapshot through a closed family registry."""
    from mountainash.core.errors import BackendConversionError

    identity = native.value_identity
    adapter = LOGICAL_SNAPSHOT_ADAPTERS.get(identity.family)
    if adapter is None:
        raise BackendConversionError(
            "logical_terminal_snapshot() has no declared native extraction route",
            boundary_key=None,
            source_family=str(identity.family),
            source_dialect=identity.dialect,
            destination_family=None,
            destination_dialect=None,
            source_type=type(native.value).__name__,
            route="logical_terminal_snapshot",
            reason="unregistered logical snapshot adapter",
        )
    return adapter.snapshot(native)


def resolved_snapshot_to_polars(resolved: ResolvedLogicalSnapshot) -> "pl.DataFrame":
    """Reconstruct a Polars frame from one resolved logical snapshot,
    retaining untagged-column dtypes and tagging transported columns
    ``pl.Object`` (spec Task 4 step 6)."""
    adapter = LOGICAL_SNAPSHOT_ADAPTERS[resolved.physical.source_identity.family]
    return adapter.to_polars(resolved)


def logical_column_values(
    resolved: ResolvedLogicalSnapshot, field_name: str
) -> "tuple[Any, ...]":
    """One retained field's values as genuinely Python-native scalars:
    ``None`` for every null representation (pandas NaN/NaT/pd.NA, PyArrow
    null), PyArrow ``Scalar`` objects unwrapped via ``.as_py()`` (spec
    section 15's identity/uniqueness consumers).

    A transported field's logical column is already Python-native --
    ``resolve_structured_cell()`` only ever receives and returns
    normalized Python values. An untagged (passthrough) field keeps its
    adapter-captured backend-native Series/ChunkedArray so the dtype-
    preserving egress path (spec Task 4 step 6) can identity-check it
    against the physical column; this accessor normalizes a READ of that
    column without mutating ``ResolvedLogicalSnapshot`` itself.
    """
    column = resolved.logical_columns[field_name]
    if column is not resolved.physical.columns.get(field_name):
        return tuple(_python_value(value) for value in column)
    family = resolved.physical.source_identity.family
    column = _slice_native(family, column, _keep_positions(resolved))
    if family is CONST_BACKEND.PANDAS:
        import pandas as pd

        return tuple(None if pd.isna(value) else value for value in column)
    if family is CONST_BACKEND.POLARS:
        return tuple(column)
    return tuple(_python_value(value) for value in column)


def _native_column_to_arrow(family: CONST_BACKEND, column: Any) -> Any:
    import pyarrow as pa

    if family is CONST_BACKEND.PANDAS:
        return pa.Array.from_pandas(column)
    if family is CONST_BACKEND.POLARS:
        return column.to_arrow()
    return column


def logical_to_arrow(resolved: ResolvedLogicalSnapshot) -> "pa.Table":
    """Arrow table of one resolved logical snapshot, in the physical column order.

    Untagged columns keep their physical Arrow type; transported columns are
    built from their Python-native logical values with the resolved target
    type. A logical value Arrow cannot represent raises ``BackendConversionError``.
    """
    import pyarrow as pa

    from mountainash.core.errors import BackendConversionError

    identity = resolved.physical.source_identity
    family = identity.family if identity is not None else None
    positions = _keep_positions(resolved)
    names = [*resolved.physical.columns, *(n for n in resolved.logical_columns if n not in resolved.physical.columns)]
    columns: dict[str, Any] = {}
    for name in names:
        logical = resolved.logical_columns[name]
        if logical is resolved.physical.columns.get(name):
            columns[name] = _native_column_to_arrow(family, _slice_native(family, logical, positions))
            continue
        try:
            columns[name] = pa.array(
                [v.as_py() if isinstance(v, pa.Scalar) else v for v in logical],
                type=resolved.target_dtypes.get(name),
            )
        except (pa.ArrowInvalid, pa.ArrowTypeError) as error:
            raise BackendConversionError(
                f"logical column {name!r} is not Arrow-representable: {error}",
                boundary_key=None,
                source_family=str(family),
                source_dialect=identity.dialect if identity is not None else None,
                destination_family="pyarrow",
                destination_dialect="pyarrow",
                source_type="logical column",
                route="logical_to_arrow",
                reason="logical value not Arrow-representable",
            ) from error
    return pa.table(columns)


def resolved_snapshot_to_pandas(resolved: ResolvedLogicalSnapshot) -> Any:
    """Reconstruct a pandas frame from one resolved logical snapshot,
    retaining untagged-column dtypes and giving transported columns
    ``dtype=object`` (spec Task 4 step 6)."""
    adapter = LOGICAL_SNAPSHOT_ADAPTERS[resolved.physical.source_identity.family]
    return adapter.to_pandas(resolved)


__all__ = [
    "LogicalSnapshotAdapter",
    "LogicalTerminalSnapshot",
    "ResolvedLogicalSnapshot",
    "logical_column_values",
    "logical_terminal_snapshot",
    "logical_to_arrow",
    "resolve_logical_snapshot",
    "resolved_snapshot_to_pandas",
    "resolved_snapshot_to_polars",
]
