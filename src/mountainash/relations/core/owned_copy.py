"""Independent native values and owner-thread, committed physical cleanup."""
from __future__ import annotations

from dataclasses import dataclass, field
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
    """A native value cannot be copied with independent, preserved contents."""


_pending_lock = threading.Lock()
_pending: dict[int, tuple[Any, list[tuple[int, str]]]] = {}


@dataclass(eq=False)
class _OwnedState:
    closed: bool = False
    anchors: set[int] = field(default_factory=set)
    physical_key: tuple[int, str] | None = None
    on_unreachable: Callable[[], None] | None = None


_states: dict[int, tuple[Any, _OwnedState]] = {}
_physical_states: dict[tuple[int, str], _OwnedState] = {}


def _bind_state(anchor, state):
    key = id(anchor)
    prior = _states.get(key)
    if prior is not None and prior[0]() is anchor:
        return
    state.anchors.add(key)

    def forget(reference):
        if _states.get(key, (None,))[0] is reference:
            del _states[key]
            state.anchors.discard(key)
            if not state.anchors and state.physical_key is not None:
                _physical_states.pop(state.physical_key, None)
                if state.on_unreachable is not None:
                    state.on_unreachable()

    reference = weakref.ref(anchor)
    _states[key] = (reference, state)
    # Bookkeeping survives explicit release; only the physical handoff callback
    # is detached then. No callback retains this anchor or any equivalent alias.
    weakref.finalize(anchor, forget, reference)


def bind_owned_alias(alias: Any, original: Any) -> None:
    """The finished native expression shares the original copy's logical state."""
    states = owned_dependencies(original)
    if len(states) == 1:
        _bind_state(alias.op() if is_ibis_table(alias) else alias, states[0])


def owned_dependencies(native: Any) -> tuple[Any, ...]:
    """Return live owned states reached by a native leaf or Ibis op graph."""
    anchors = [native]
    if is_ibis_table(native):
        from mountainash.core.lazy_imports import import_ibis_expr_ops
        anchors = [native.op(), *native.op().find(import_ibis_expr_ops().DatabaseTable)]
    found = []
    for anchor in anchors:
        entry = _states.get(id(anchor))
        state = entry[1] if entry is not None and entry[0]() is anchor else None
        if state is None and hasattr(anchor, "source") and hasattr(anchor, "name"):
            state = _physical_states.get((id(anchor.source), anchor.name))
            if state is not None:
                _bind_state(anchor, state)
        if state is not None and state not in found:
            found.append(state)
    return tuple(found)


def assert_owned_open(native: Any) -> None:
    from mountainash.relations.core.errors import MaterializationScopeClosedError
    if any(state.closed for state in owned_dependencies(native)):
        raise MaterializationScopeClosedError("snapshot's materialization scope is closed")


def invalidate_owned(native: Any) -> None:
    for state in owned_dependencies(native):
        state.closed = True


def assert_prepared_owned_open(prepared: Any) -> None:
    """Inspect existing expanded leaves, including refs, before compilation."""
    from mountainash.relations.core.relation_nodes import ReadRelNode
    for node in prepared.nodes.values():
        if isinstance(node, ReadRelNode):
            assert_owned_open(node.dataframe)


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
    state = _OwnedState(physical_key=(id(connection), name))
    _physical_states[state.physical_key] = state
    handed_off = False

    def enqueue():
        nonlocal handed_off
        with _pending_lock:
            if not handed_off:
                _enqueue(connection, owner, name)
                handed_off = True

    state.on_unreachable = enqueue
    _bind_state(table.op(), state)

    def release():
        enqueue()
        state.on_unreachable = None
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
    for name, dtype in value.schema.items():
        if dtype == pl.Object:
            raise UnownableSnapshotValueError(f"Cannot independently own Polars Object column {name!r}")
    arrow = transit_call(BoundaryKey.OWNED_COPY_POLARS_TO_ARROW, value.to_arrow)
    return pl.from_arrow(ipc_copy(arrow), rechunk=False)


def _pandas_copy(value):
    pd, np, pa = import_pandas(), import_numpy(), import_pyarrow()
    from datetime import date, datetime, time, timedelta
    from decimal import Decimal
    from fractions import Fraction

    immutable = {type(None), bool, int, float, complex, str, bytes, date, datetime,
                 time, timedelta, Decimal, Fraction, pd.Timestamp, pd.Timedelta}

    def supported(cell):
        if type(cell) in immutable or cell is pd.NA or cell is pd.NaT:
            return True
        if type(cell) in (tuple, frozenset):
            return all(supported(child) for child in cell)
        # NumPy scalar values, unlike void scalars, cannot borrow mutable fields.
        return type(cell).__module__ == "numpy" and isinstance(
            cell, (np.number, np.bool_, np.str_, np.bytes_, np.datetime64, np.timedelta64)
        )

    def validate(values, label):
        if any(not supported(cell) for cell in values):
            raise UnownableSnapshotValueError(f"Cannot own mutable or unsupported object values in {label}")

    def index_copy(index):
        if isinstance(index, pd.MultiIndex):
            return pd.MultiIndex(levels=[index_copy(level) for level in index.levels],
                                 codes=[code.copy() for code in index.codes],
                                 names=index.names, sortorder=index.sortorder)
        if isinstance(index, pd.CategoricalIndex):
            array = pd.Categorical.from_codes(index.codes.copy(), index_copy(index.categories),
                                             ordered=index.ordered)
            return pd.CategoricalIndex(array, name=index.name)
        if pd.api.types.is_object_dtype(index.dtype):
            validate(index, f"index {index.name!r}")
        if hasattr(index.array, "__arrow_array__"):
            arrow = ipc_copy(pa.table({"index": index.array.__arrow_array__()}))["index"]
            return pd.Index(pd.array(arrow, dtype=index.dtype), name=index.name)
        return index.copy(deep=True)

    for name, series in value.items():
        if pd.api.types.is_object_dtype(series.dtype):
            validate(series, f"column {name!r}")
        elif isinstance(series.dtype, pd.CategoricalDtype):
            validate(series.cat.categories, f"column {name!r} categories")
    result = value.copy(deep=True)
    result.index = index_copy(value.index)
    result.columns = index_copy(value.columns)
    for index, (_, series) in enumerate(value.items()):
        if isinstance(series.dtype, pd.CategoricalDtype):
            result.isetitem(index, pd.Categorical.from_codes(
                series.cat.codes.to_numpy(copy=True), index_copy(series.cat.categories),
                ordered=series.cat.ordered,
            ))
        elif hasattr(series.array, "__arrow_array__"):
            arrow = pa.table({"value": series.array.__arrow_array__()})
            copied = transit_call(
                BoundaryKey.OWNED_COPY_PANDAS_SERIES, pd.Series,
                ipc_copy(arrow)["value"], index=result.index, name=series.name, dtype=series.dtype,
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
    value = transit_call(BoundaryKey.OWNED_COPY, _inprocess_copy, native)
    _bind_state(value, _OwnedState())
    return OwnedCopy(value)


def require_copy_idle(connection: Any) -> None:
    """Admit known SQL copy work without draining or acquiring a transaction."""
    if connection is None or connection.name == "polars":
        return
    from mountainash.relations.backends.relation_systems.ibis._physical import adopt_connection, require_idle
    with adopt_connection(connection) as backend:
        require_idle(backend)


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
