# tests/relations/dag/test_dag_count_rows_and_item.py
"""DAG integration for count_rows() and item() terminals."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations import relation
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag.errors import RelationDAGRequired


def test_count_rows_standalone_on_ref_raises():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}, {"id": 2}]))
    ref_rel = dag.ref("orders")
    with pytest.raises(RelationDAGRequired):
        ref_rel.count_rows()


def test_item_standalone_on_ref_raises():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}]))
    ref_rel = dag.ref("orders")
    with pytest.raises(RelationDAGRequired):
        ref_rel.item("id")


def test_dag_collect_then_count_rows():
    dag = RelationDAG()
    dag.add("orders", relation([{"id": 1}, {"id": 2}, {"id": 3}]))
    dag.add(
        "filtered",
        dag.ref("orders").filter(ma.col("id").gt(ma.lit(1))),
    )
    native = dag.collect("filtered")
    df = native.collect() if isinstance(native, pl.LazyFrame) else native
    assert len(df) == 2


def test_dag_collect_then_item():
    dag = RelationDAG()
    dag.add(
        "orders",
        relation([{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]),
    )
    dag.add("first", dag.ref("orders").head(1))
    native = dag.collect("first")
    df = native.collect() if isinstance(native, pl.LazyFrame) else native
    # Wrap the native back in a Relation to use item()
    assert relation(df).item("name") == "alice"
