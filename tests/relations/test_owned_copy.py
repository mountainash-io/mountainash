"""Owned-copy independence and lifetime at real native/backend boundaries."""
from __future__ import annotations

import numpy as np
import gc
import threading
import uuid
from contextlib import contextmanager
import ibis
import pandas as pd
import polars as pl
import pyarrow as pa
import narwhals as nw
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS, REGISTRY
from mountainash.core.transit import BoundaryKey, capture_conversion_trace
from mountainash.relations.core.owned_copy import owned_copy, UnownableSnapshotValueError
from mountainash.relations.backends.relation_systems.ibis._physical import adopt_connection, owned_transaction

pytest_plugins = ("fixtures.ibis_physical",)


def _catalog(connection):
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            return backend.list_tables()


def test_sql_copy_survives_source_deletion_and_derived_plan(connection):
    from mountainash.relations.core.owned_copy import drain_pending_drops
    name = "source_" + uuid.uuid4().hex
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table(name, ibis.memtable({"x": [7]}), temp=True)
            source = backend.table(name)
    copy = owned_copy(source)
    owned_name = copy.value.op().name
    derived = copy.value.filter(copy.value.x > 0)
    del copy
    gc.collect()
    drain_pending_drops(connection)
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.drop_table(name)
            assert backend.run_expr(derived)["x"].tolist() == [7]
    del derived
    gc.collect()
    drain_pending_drops(connection)
    assert owned_name not in _catalog(connection)


@pytest.mark.parametrize("explicit", [False, True])
def test_worker_release_only_enqueues(connection, explicit):
    from mountainash.relations.core.owned_copy import drain_pending_drops
    name = "source_" + uuid.uuid4().hex
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table(name, ibis.memtable({"x": [7]}), temp=True)
            source = backend.table(name)
    held = [owned_copy(source)]
    target = held[0].value.op().name
    errors = []

    def worker():
        try:
            value = held.pop()
            if explicit:
                value.release()
                value.release()
            del value
            gc.collect()
            drain_pending_drops(connection)
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    assert errors == []
    assert target in _catalog(connection)
    drain_pending_drops(connection)
    assert target not in _catalog(connection)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("empty", [False, True])
def test_copy_preserves_values_and_schema(backend_name, empty):
    source = REGISTRY[backend_name].build({"x": [7]}, "owned_schema_source")
    rel = ma.relation(source)
    if empty:
        rel = rel.filter(ma.col("x") < 0)
    native = rel.collect(unwrap=False)
    with capture_conversion_trace() as trace:
        copy = owned_copy(native)
    assert sum(record.boundary_key is BoundaryKey.OWNED_COPY for record in trace.records) == 1
    try:
        assert ma.relation(copy.value).to_dicts() == ([] if empty else [{"x": 7}])
        assert ma.relation(copy.value).schema == rel.schema
    finally:
        if copy.release is not None:
            copy.release()


@pytest.mark.parametrize("kind", ["polars", "pandas", "pandas-arrow", "arrow", "narwhals-arrow"])
def test_copy_severs_external_primitive_buffer(kind):
    """Each case targets its native buffer owner, not expression semantics."""
    values = np.array([7], dtype=np.int64)
    if kind == "polars":
        source = pl.DataFrame(pl.Series("x", values))
    elif kind == "pandas":
        source = pd.DataFrame({"x": values}, copy=False)
    elif kind == "pandas-arrow":
        source = pd.DataFrame({"x": pd.Series(pa.array(values), dtype=pd.ArrowDtype(pa.int64()))})
    else:
        source = pa.table({"x": pa.array(values)})
        if kind == "narwhals-arrow":
            source = nw.from_native(source)
    with capture_conversion_trace() as trace:
        copy = owned_copy(source)
    keys = {record.boundary_key for record in trace.records}
    if kind == "polars":
        assert BoundaryKey.OWNED_COPY_POLARS_TO_ARROW in keys
    elif kind == "pandas-arrow":
        assert BoundaryKey.OWNED_COPY_PANDAS_SERIES in keys
    values[0] = 88
    if kind == "polars":
        # Read buffers directly: lazy optimizations may reuse pre-mutation stats.
        assert source["x"].to_list() == [88]
        assert copy.value["x"].to_list() == [7]
    else:
        assert ma.relation(source).to_dicts() == [{"x": 88}]
        assert ma.relation(copy.value).to_dicts() == [{"x": 7}]


@pytest.mark.parametrize("wrapped", [False, True])
def test_dictionary_payload_is_independent(wrapped):
    data = bytearray(b"a")
    dictionary = pa.Array.from_buffers(pa.string(), 1, [
        None, pa.py_buffer(np.array([0, 1], dtype=np.int32)), pa.py_buffer(data),
    ])
    table = pa.table({"x": pa.DictionaryArray.from_arrays(pa.array([0], pa.int32()), dictionary)})
    source = nw.from_native(table) if wrapped else table
    copy = owned_copy(source)
    data[0] = ord("z")
    assert ma.relation(source).to_dicts() == [{"x": "z"}]
    assert ma.relation(copy.value).to_dicts() == [{"x": "a"}]
    actual = copy.value.to_native() if wrapped else copy.value
    assert actual.schema == table.schema


def test_nested_arrow_children_are_independent():
    values = np.array([7], dtype=np.int64)
    child = pa.array(values)
    lists = pa.ListArray.from_arrays(pa.array([0, 1], pa.int32()), child)
    source = pa.table({"payload": pa.StructArray.from_arrays([lists], names=["items"])})
    copy = owned_copy(source)
    values[0] = 88
    assert source.to_pylist() == [{"payload": {"items": [88]}}]
    assert copy.value.to_pylist() == [{"payload": {"items": [7]}}]


@pytest.mark.parametrize("cell", [[1], {"x": 1}, {1}, bytearray(b"a"), np.array([1]), ([1],)])
def test_pandas_mutable_object_is_refused(cell):
    source = pd.DataFrame({"payload": pd.Series([cell], dtype=object)})
    with pytest.raises(UnownableSnapshotValueError, match="payload"):
        owned_copy(source)


def test_pandas_copy_preserves_index_and_immutable_object_cells():
    source = pd.DataFrame({"x": pd.Series([(1, "a"), None], dtype=object)})
    source.index = pd.Index([9, 4], name="row")
    copy = owned_copy(source)
    source.iloc[0, 0] = "changed"
    assert copy.value["x"].tolist() == [(1, "a"), None]
    assert copy.value.index.tolist() == [9, 4]
    assert copy.value.index.name == "row"


class MutableCell:
    def __init__(self):
        self.value = 7


@pytest.mark.parametrize("cell,categorical", [
    (memoryview(bytearray(b"a")), False), (MutableCell(), False), (MutableCell(), True),
])
def test_pandas_unknown_mutable_cells_are_refused(cell, categorical):
    series = pd.Series([cell], dtype=object)
    if categorical:
        series = series.astype("category")
    source = pd.DataFrame({"payload": series})
    with pytest.raises(UnownableSnapshotValueError, match="payload"):
        owned_copy(source)


def test_polars_object_columns_never_publish_pointer_bytes():
    source = pl.DataFrame(pl.Series("payload", ["hello"], dtype=pl.Object))
    with pytest.raises(UnownableSnapshotValueError, match="payload"):
        ma.relation(source).snapshot()


def test_pandas_categorical_column_owns_unused_categories_and_order():
    values = np.array([7, 8, 9], dtype=np.int64)
    source = pd.DataFrame({"x": pd.Categorical.from_codes(
        [0, 1], categories=pd.Index(values, copy=False), ordered=True,
    )})
    saved = ma.relation(source).snapshot()
    values[0] = 88
    values[2] = 99
    assert source.x.tolist() == [88, 8]
    result = saved.collect()
    assert result.x.tolist() == [7, 8]
    assert result.x.cat.categories.tolist() == [7, 8, 9]
    assert result.x.cat.ordered is True


@pytest.mark.parametrize("kind", ["integer", "arrow", "multi"])
def test_pandas_index_buffers_are_independent(kind):
    values = np.array([7, 8], dtype=np.int64)
    if kind == "integer":
        index = pd.Index(values, copy=False, name="row")
    elif kind == "arrow":
        index = pd.Index(pa.array(values), dtype=pd.ArrowDtype(pa.int64()), name="row")
    else:
        index = pd.MultiIndex(levels=[pd.Index(values, copy=False), ["a"]],
                              codes=[[0, 1], [0, 0]], names=["row", "label"])
    source = pd.DataFrame({"x": [1, 2]}, index=index)
    copy = owned_copy(source)
    values[0] = 88
    assert source.index.tolist() == ([(88, "a"), (8, "a")] if kind == "multi" else [88, 8])
    assert copy.value.index.tolist() == ([(7, "a"), (8, "a")] if kind == "multi" else [7, 8])
    assert copy.value.index.names == source.index.names
    assert type(copy.value.index) is type(source.index)


@pytest.mark.parametrize("completion", ["COMMIT", "ROLLBACK"])
def test_pending_release_survives_caller_transaction(connection, completion):
    from mountainash.relations.core.owned_copy import drain_pending_drops
    name = "source_" + uuid.uuid4().hex
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table(name, ibis.memtable({"x": [7]}), temp=True)
            source = backend.table(name)
    copy = owned_copy(source)
    target = copy.value.op().name
    # Test-owned driver models a caller transaction; production never uses it.
    def sql(statement):
        if connection.name == "postgres":
            with connection.con.cursor() as cursor:
                cursor.execute(statement)
        else:
            connection.con.execute(statement)
    sql("BEGIN")
    try:
        copy.release()
        del copy
        gc.collect()
        drain_pending_drops(connection)
        with adopt_connection(connection) as backend:
            assert backend.native_transaction_open() is True
    finally:
        sql(completion)
    assert target in _catalog(connection)
    drain_pending_drops(connection)
    assert target not in _catalog(connection)


def test_ambiguous_cleanup_completion_keeps_identifier_for_retry(connection, monkeypatch):
    from mountainash_data import IbisBackend
    from mountainash.relations.core.owned_copy import drain_pending_drops
    name = "source_" + uuid.uuid4().hex
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table(name, ibis.memtable({"x": [7]}), temp=True)
            source = backend.table(name)
    copy = owned_copy(source)
    target = copy.value.op().name
    transaction = IbisBackend.transaction
    drop = IbisBackend.drop_table
    failure = RuntimeError("completion receipt lost")
    dropped = []

    @contextmanager
    def ambiguous(self, *args, **kwargs):
        with transaction(self, *args, **kwargs) as current:
            yield current
        raise failure

    def record_drop(self, table_name, *args, **kwargs):
        dropped.append(table_name)
        return drop(self, table_name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(IbisBackend, "transaction", ambiguous)
        with pytest.raises(RuntimeError) as caught:
            copy.release()
        assert caught.value is failure
    del copy
    gc.collect()
    # A real committed delete happened, but without a receipt we must retry it.
    monkeypatch.setattr(IbisBackend, "drop_table", record_drop)
    drain_pending_drops(connection)
    assert dropped == [target]
    assert target not in _catalog(connection)
    drain_pending_drops(connection)
    assert dropped == [target]


def test_ibis_polars_severs_buffer_before_registering():
    connection = ibis.polars.connect()
    values = np.array([7], dtype=np.int64)
    source = connection.create_table("source", pl.DataFrame(pl.Series("x", values)))
    copy = owned_copy(source)
    try:
        values[0] = 88
        assert ma.relation(source).to_dicts() == [{"x": 88}]
        connection.drop_table("source")
        assert ma.relation(copy.value).to_dicts() == [{"x": 7}]
    finally:
        copy.release()
        connection.disconnect()
