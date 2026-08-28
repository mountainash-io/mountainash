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
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.transit import BoundaryKey, transit_call

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    import pandas as pd
    import polars as pl

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
                columns[name] = pl.Series(name, transported[name], dtype=pl.Object)
            else:
                columns[name] = _native_column_to_polars(self.family, untagged[name])
        return pl.DataFrame(columns)

    def to_pandas(self, resolved: ResolvedLogicalSnapshot) -> Any:
        import pandas as pd

        names, transported, untagged = self._output_columns(resolved)
        columns: dict[str, Any] = {}
        for name in names:
            if name in transported:
                columns[name] = transit_call(
                    BoundaryKey.LOGICAL_SNAPSHOT_PANDAS_FRAME_ASSEMBLY,
                    pd.Series,
                    transported[name],
                    dtype=object,
                )
            else:
                columns[name] = _native_column_to_pandas(self.family, untagged[name])
        return transit_call(
            BoundaryKey.LOGICAL_SNAPSHOT_PANDAS_FRAME_ASSEMBLY, pd.DataFrame, columns
        )


def _native_column_to_polars(family: CONST_BACKEND, column: Any) -> "pl.Series":
    import polars as pl

    if family is CONST_BACKEND.POLARS:
        return cast("pl.Series", column)
    if family is CONST_BACKEND.PANDAS:
        return cast(
            "pl.Series",
            transit_call(BoundaryKey.LOGICAL_SNAPSHOT_PANDAS_TO_POLARS, pl.from_pandas, column),
        )
    return cast(
        "pl.Series",
        transit_call(BoundaryKey.LOGICAL_SNAPSHOT_ARROW_TO_POLARS, pl.from_arrow, column),
    )


def _native_column_to_pandas(family: CONST_BACKEND, column: Any) -> "pd.Series":
    if family is CONST_BACKEND.PANDAS:
        return cast("pd.Series", column)
    if family is CONST_BACKEND.POLARS:
        return cast(
            "pd.Series",
            transit_call(BoundaryKey.LOGICAL_SNAPSHOT_POLARS_TO_PANDAS, column.to_pandas),
        )
    return cast(
        "pd.Series",
        transit_call(BoundaryKey.LOGICAL_SNAPSHOT_ARROW_TO_PANDAS, column.to_pandas),
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
        arrow = transit_call(BoundaryKey.LOGICAL_SNAPSHOT_NARWHALS_TO_ARROW, native.value.to_arrow)
        return _snapshot_from_columns(
            native, {name: arrow.column(name) for name in arrow.column_names}
        )


class _IbisSnapshotAdapter(_BaseSnapshotAdapter):
    family = CONST_BACKEND.IBIS

    def snapshot(self, native: Any) -> LogicalTerminalSnapshot:
        arrow = transit_call(BoundaryKey.LOGICAL_SNAPSHOT_IBIS_TO_ARROW, native.value.to_pyarrow)
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
    """Normalize one physical cell to a Python-native scalar before
    structured resolution. PyArrow-native snapshot columns (the PyArrow,
    Narwhals, and Ibis adapters all capture Arrow columns) yield ``Scalar``
    wrapper objects when iterated, not the underlying Python value the
    shared decoder expects; every other adapter's native sequence type
    already yields native Python scalars."""
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

    resolved_transport: dict[str, tuple[Any, ...]] = {}
    keep = [True] * row_count
    for field_name, plan in plans.items():
        physical = snapshot.columns.get(field_name)
        if physical is None:
            continue
        values: list[Any] = []
        for index, value in enumerate(physical):
            resolution = resolve_structured_cell(_python_value(value), plan=plan, consumer=consumer)
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
    return transit_call(BoundaryKey.LOGICAL_SNAPSHOT_POLARS_DISPATCH, adapter.to_polars, resolved)


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
        return tuple(column)
    family = resolved.physical.source_identity.family
    if family is CONST_BACKEND.PANDAS:
        import pandas as pd

        return tuple(None if pd.isna(value) else value for value in column)
    if family is CONST_BACKEND.POLARS:
        return tuple(column)
    return tuple(_python_value(value) for value in column)


def resolved_snapshot_to_pandas(resolved: ResolvedLogicalSnapshot) -> Any:
    """Reconstruct a pandas frame from one resolved logical snapshot,
    retaining untagged-column dtypes and giving transported columns
    ``dtype=object`` (spec Task 4 step 6)."""
    adapter = LOGICAL_SNAPSHOT_ADAPTERS[resolved.physical.source_identity.family]
    return transit_call(BoundaryKey.LOGICAL_SNAPSHOT_PANDAS_DISPATCH, adapter.to_pandas, resolved)


__all__ = [
    "LogicalSnapshotAdapter",
    "LogicalTerminalSnapshot",
    "ResolvedLogicalSnapshot",
    "logical_column_values",
    "logical_terminal_snapshot",
    "resolve_logical_snapshot",
    "resolved_snapshot_to_pandas",
    "resolved_snapshot_to_polars",
]
