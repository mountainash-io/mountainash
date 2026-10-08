"""Independent native values and owner-thread, committed physical cleanup."""
from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import TYPE_CHECKING, Any
import uuid
import weakref

from mountainash.core.lazy_imports import import_narwhals, import_numpy, import_pandas, import_polars, import_pyarrow
from mountainash.core.transit import BoundaryKey, transit_call
from mountainash.core.types import (
    BackendCapabilityError, is_ibis_table, is_narwhals_dataframe,
    is_narwhals_lazyframe, is_pandas_dataframe, is_polars_dataframe,
    is_polars_lazyframe, is_pyarrow_table,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


@dataclass(frozen=True)
class OwnedCopy:
    value: Any
    release: Callable[[], None] | None = None


class UnownableSnapshotValueError(TypeError):
    """A pandas object cell contains mutable state we cannot independently own."""


_pending_lock = threading.Lock()
_pending: dict[int, tuple[Any, list[tuple[int, str]]]] = {}


def enqueue_owned_drop(connection: Any, owner_thread: int, name: str) -> None:
    """Transfer an unreused identifier to the queue without database calls."""
    with _pending_lock:
        _enqueue(connection, owner_thread, name)


def _enqueue(connection, owner_thread, name):
    entry = _pending.setdefault(id(connection), (connection, []))
    item = (owner_thread, name)
    if item not in entry[1]:
        entry[1].append(item)


def drain_pending_drops(connection: Any) -> None:
    """Retire only this thread's identifiers after committed deletion."""
    owner = threading.get_ident()
    with _pending_lock:
        entry = _pending.get(id(connection))
        names = tuple(name for thread, name in entry[1] if thread == owner) if entry else ()
    if not names:
        return
    if connection.name == "polars":
        for name in names:
            connection.drop_table(name, force=True)
    else:
        from mountainash.relations.backends.relation_systems.ibis._physical import drop_owned_tables
        if not drop_owned_tables(connection, names):
            return
    completed = set(names)
    with _pending_lock:
        entry = _pending[id(connection)]
        entry[1][:] = [(thread, name) for thread, name in entry[1]
                      if not (thread == owner and name in completed)]
        if not entry[1]:
            del _pending[id(connection)]


def register_owned_ibis_table(connection: Any, name: str, table: Any) -> OwnedCopy:
    """Anchor cleanup to the physical op so derived expressions retain it."""
    owner = threading.get_ident()
    handed_off = False

    def enqueue():
        nonlocal handed_off
        with _pending_lock:
            if not handed_off:
                _enqueue(connection, owner, name)
                handed_off = True

    finalizer = weakref.finalize(table.op(), enqueue)

    def release():
        enqueue()
        finalizer.detach()
        if threading.get_ident() == owner:
            drain_pending_drops(connection)

    return OwnedCopy(table, release)


def ipc_copy(table: Any) -> Any:
    """Copy all Arrow buffers, including dictionaries and nested children."""
    pa = import_pyarrow()
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return pa.ipc.open_stream(sink.getvalue()).read_all()


def _polars_copy(value):
    pl = import_polars()
    if is_polars_lazyframe(value):
        value = transit_call(BoundaryKey.POLARS_LAZY_COLLECT, value.collect)
    arrow = transit_call(BoundaryKey.OWNED_COPY_POLARS_TO_ARROW, value.to_arrow)
    return pl.from_arrow(ipc_copy(arrow), rechunk=False)


def _pandas_copy(value):
    pd, np, pa = import_pandas(), import_numpy(), import_pyarrow()

    def mutable(cell):
        if isinstance(cell, (list, dict, set, bytearray, np.ndarray)):
            return True
        if isinstance(cell, (tuple, frozenset)):
            return any(mutable(child) for child in cell)
        return False

    for name, series in value.items():
        if pd.api.types.is_object_dtype(series.dtype) and any(mutable(cell) for cell in series):
            raise UnownableSnapshotValueError(f"Cannot own mutable object values in column {name!r}")
    result = value.copy(deep=True)
    for index, (_, series) in enumerate(value.items()):
        if hasattr(series.array, "__arrow_array__"):
            arrow = pa.table({"value": series.array.__arrow_array__()})
            copied = transit_call(
                BoundaryKey.OWNED_COPY_PANDAS_SERIES, pd.Series,
                ipc_copy(arrow)["value"], index=series.index, name=series.name, dtype=series.dtype,
            )
            result.isetitem(index, copied)
    return result


def _inprocess_copy(value):
    if is_polars_dataframe(value) or is_polars_lazyframe(value):
        return _polars_copy(value)
    if is_pandas_dataframe(value):
        return _pandas_copy(value)
    if is_pyarrow_table(value):
        return ipc_copy(value)
    if is_narwhals_lazyframe(value):
        value = transit_call(BoundaryKey.NARWHALS_LAZY_COLLECT, value.collect)
    if is_narwhals_dataframe(value):
        nw = import_narwhals()
        if value.implementation.is_pandas():
            native = transit_call(BoundaryKey.NARWHALS_NATIVE_UNWRAP_PANDAS, value.to_native)
        else:
            native = transit_call(BoundaryKey.NARWHALS_NATIVE_UNWRAP_NON_PANDAS, value.to_native)
        return transit_call(BoundaryKey.NARWHALS_NATIVE_WRAP, nw.from_native, _inprocess_copy(native))
    raise TypeError(f"Unsupported owned-copy value: {type(value).__name__}")


def owned_copy(native: Any) -> OwnedCopy:
    """Copy once in the source's native backend, with no shared source buffers."""
    if is_ibis_table(native):
        return owned_ibis_table(native)
    return OwnedCopy(transit_call(BoundaryKey.OWNED_COPY, _inprocess_copy, native))


def owned_ibis_table(expr: Any) -> OwnedCopy:
    """Copy on the explicit bound connection; never infer a default backend."""
    try:
        connection = expr._find_backend(use_default=False)
    except Exception as exc:
        raise BackendCapabilityError(
            "Owned copy requires an explicit connection", backend="ibis", function_key="OWNED_COPY",
        ) from exc
    if connection.name != "polars":
        return owned_sql_batch(connection, (expr,))[0]
    drain_pending_drops(connection)
    name = "ma_owned_" + uuid.uuid4().hex
    try:
        def copy():
            frame = _polars_copy(connection.compile(expr))
            return connection.create_table(name, frame)
        table = transit_call(BoundaryKey.OWNED_COPY, copy)
        return register_owned_ibis_table(connection, name, table)
    except BaseException as original:
        _failed_copy(connection, (name,), original)
        raise


def _failed_copy(connection, names, original):
    for name in names:
        enqueue_owned_drop(connection, threading.get_ident(), name)
    try:
        drain_pending_drops(connection)
    except BaseException as cleanup:
        original.add_note(f"Owned-copy cleanup also failed: {type(cleanup).__name__}")


def owned_sql_batch(connection: Any, expressions: Sequence[Any]) -> tuple[OwnedCopy, ...]:
    """Typed create/insert/bind in one admitted unit; publish only after exit."""
    if not expressions:
        return ()
    from mountainash.relations.backends.relation_systems.ibis._physical import (
        adopt_connection, owned_transaction, require_idle,
    )
    attempted, tables, copies = [], [], []
    with adopt_connection(connection) as backend:
        require_idle(backend)
        drain_pending_drops(connection)
        try:
            with owned_transaction(backend):
                for expr in expressions:
                    name = "ma_owned_" + uuid.uuid4().hex
                    attempted.append(name)

                    def copy():
                        backend.create_table(name, None, schema=expr.schema(), temp=True)
                        backend.insert(name, expr)
                        return backend.table(name)

                    tables.append(transit_call(BoundaryKey.OWNED_COPY, copy))
            for name, table in zip(attempted, tables):
                copies.append(register_owned_ibis_table(connection, name, table))
            return tuple(copies)
        except BaseException as original:
            _failed_copy(connection, attempted, original)
            for copy in copies:
                try:
                    copy.release()
                except BaseException as cleanup:
                    original.add_note(f"Owned-copy release also failed: {type(cleanup).__name__}")
            raise
