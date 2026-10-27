"""Native endpoints, connection-preserving to_ibis, logical Arrow terminal."""
from __future__ import annotations

import ibis
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
from ibis.expr import operations as ops

import mountainash as ma
from mountainash.core.errors import BackendConversionError
from mountainash.relations.core.logical_snapshot import (
    LogicalTerminalSnapshot,
    ResolvedLogicalSnapshot,
    logical_to_arrow,
)
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType


@pytest.fixture
def structured_rel():
    df = pl.DataFrame({"tags": ["[1,2]", "[3]"], "name": ["a", "b"]})
    spec = TableSchema(
        fields_match="open", fields={"tags": FieldDefinition(type=UniversalType.ARRAY)}
    )
    return ma.relation(df).conform(spec, contract={"data_type": "coerce"})


def test_to_pandas_native_mixed_objects():
    df = pd.DataFrame({"id": [1, 2], "obj": [{"a": 1}, [1, 2]]}, index=pd.Index([10, 20], name="k"))
    out = ma.relation(df).to_pandas()
    assert out.index.name == "k" and out["obj"].iloc[0] is df["obj"].iloc[0]


def test_to_ibis_keeps_connection():
    con = ibis.duckdb.connect()
    assert ma.from_arrow(pa.table({"id": [1, 2]}), target=con).to_ibis().get_backend() is con


def test_to_ibis_from_polars_memtable():
    assert isinstance(ma.relation(pl.DataFrame({"id": [1]})).to_ibis().op(), ops.InMemoryTable)


def test_to_polars_from_ibis_eager_no_pandas(monkeypatch):
    con = ibis.duckdb.connect()
    t = con.create_table("t", {"id": [1]})
    monkeypatch.setattr(pl, "from_pandas", lambda *a, **k: pytest.fail("pandas bridge"))
    out = ma.relation(t).to_polars()
    assert isinstance(out, pl.DataFrame) and out.to_dicts() == [{"id": 1}]


def test_to_pyarrow_logical_list(structured_rel):
    t = structured_rel.to_pyarrow()
    assert pa.types.is_list(t.schema.field("tags").type)
    assert t.column("tags").to_pylist() == [[1, 2], [3]] and t.column("name").to_pylist() == ["a", "b"]


def test_to_pyarrow_all_empty_declared_element():
    spec = TableSchema(fields_match="open", fields={
        "tags": FieldDefinition(type=UniversalType.ARRAY, element=FieldDefinition(type=UniversalType.INTEGER))})
    t = ma.relation(pl.DataFrame({"tags": ["[]", "[]"]})).conform(spec, contract={"data_type": "coerce"}).to_pyarrow()
    assert t.schema.field("tags").type == pa.list_(pa.int64())


def test_to_pyarrow_retained_rows_after_discard():
    spec = TableSchema(fields_match="open", fields={"tags": FieldDefinition(type=UniversalType.ARRAY)})
    rel = ma.relation(pl.DataFrame({"k": [1, 2, 3], "tags": ["[1]", "not json", "[3]"]})).conform(
        spec, contract={"data_type": "discard_row"})
    assert rel.to_pyarrow().column("k").to_pylist() == rel.to_pandas()["k"].tolist() == [1, 3]


def test_logical_to_arrow_unrepresentable():
    snap = ResolvedLogicalSnapshot(
        physical=LogicalTerminalSnapshot(columns={}, row_ordinals=(0, 1), source_identity=None),
        logical_columns={"x": ([1, 2], {"a": 1})}, keep_ordinals=(0, 1), target_dtypes={})
    with pytest.raises(BackendConversionError, match="not Arrow-representable"):
        logical_to_arrow(snap)


def test_structured_to_ibis_is_logical_memtable(structured_rel):
    table = structured_rel.to_ibis()
    assert isinstance(table.op(), ops.InMemoryTable)
    assert table.to_pyarrow().column("tags").to_pylist() == [[1, 2], [3]]
    assert table.to_pyarrow().column("name").to_pylist() == ["a", "b"]


def test_structured_to_ibis_unrepresentable_raises_conversion_error():
    spec = TableSchema(fields_match="open", fields={"tags": FieldDefinition(type=UniversalType.ARRAY)})
    rel = ma.relation(pl.DataFrame({"tags": ['[1,"a"]']})).conform(spec, contract={"data_type": "coerce"})
    with pytest.raises(BackendConversionError, match="not Arrow-representable"):
        rel.to_ibis()
    with pytest.raises(BackendConversionError, match="not Arrow-representable"):
        rel.to_pyarrow()


def _owned(con):
    return [n for n in con.list_tables() if n.startswith("ma_owned_")]


def _connection_dag():
    con = ibis.duckdb.connect()
    t = con.create_table("t", pa.table({"id": [1, 2, 3]}))
    dag = ma.RelationDAG()
    dag.add("a", ma.relation(t).filter(ma.col("id") > 1))
    dag.add("b", dag.ref("a").select("id"))
    return con, dag


@pytest.mark.parametrize("terminal", ["to_polars", "to_pandas", "to_pyarrow"])
def test_eager_terminals_release_dag_owned_copies(terminal):
    con, dag = _connection_dag()
    before = _owned(con)
    getattr(dag.ref("b"), terminal)()
    assert _owned(con) == before


def test_native_to_ibis_keeps_dag_owned_copies_alive():
    con, dag = _connection_dag()
    result = dag.ref("b").to_ibis()
    assert _owned(con)
    assert result.to_pyarrow().column("id").to_pylist() == [2, 3]


def test_logical_to_pandas_keeps_polars_date_column_native():
    import datetime

    spec = TableSchema(fields_match="open", fields={"tags": FieldDefinition(type=UniversalType.ARRAY)})
    df = pl.DataFrame({"tags": ["[1]"], "d": [datetime.date(2024, 1, 2)]})
    out = ma.relation(df).conform(spec, contract={"data_type": "coerce"}).to_pandas()
    assert str(out["d"].dtype).startswith("datetime64")
