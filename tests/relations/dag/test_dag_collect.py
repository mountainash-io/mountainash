"""Tests for RelationDAG.collect() — Task 17."""
from __future__ import annotations

import polars as pl
import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG


def _to_eager(result):
    if isinstance(result, pl.LazyFrame):
        return result.collect()
    return result


def test_collect_simple():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1, "amount": 10}, {"id": 2, "amount": 20}]))
    df = _to_eager(dag.collect("orders"))
    assert df["amount"].sum() == 30


def test_collect_chain():
    dag = RelationDAG()
    dag.add("orders", ma.relation([{"id": 1, "amount": 10}, {"id": 2, "amount": 20}]))
    dag.add("big", dag.ref("orders").filter(ma.col("amount").gt(15)))
    df = _to_eager(dag.collect("big"))
    assert df["id"].to_list() == [2]


def test_collect_independent_calls():
    dag = RelationDAG()
    dag.add("a", ma.relation([{"x": 1}]))
    dag.add("b", dag.ref("a"))
    dag.add("c", dag.ref("a"))
    # Two independent calls — both should work and produce equivalent results.
    rb = _to_eager(dag.collect("b"))
    rc = _to_eager(dag.collect("c"))
    assert rb["x"].to_list() == rc["x"].to_list() == [1]
