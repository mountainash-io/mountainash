"""Tests for RelationDAG.execute() — ad-hoc query execution."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG


def _to_eager(result):
    if isinstance(result, pl.LazyFrame):
        return result.collect()
    return result


def test_execute_simple_ref():
    """Execute a relation referencing one DAG table."""
    dag = RelationDAG()
    dag.add("orders", ma.relation([
        {"id": 1, "amount": 10},
        {"id": 2, "amount": 20},
    ]))
    rel = dag.ref("orders").filter(ma.col("amount").gt(15))
    df = _to_eager(dag.execute(rel))
    assert df["id"].to_list() == [2]


def test_execute_transitive_refs():
    """Execute a relation whose ref itself depends on another ref."""
    dag = RelationDAG()
    dag.add("raw", ma.relation([
        {"id": 1, "val": 5},
        {"id": 2, "val": 15},
        {"id": 3, "val": 25},
    ]))
    dag.add("filtered", dag.ref("raw").filter(ma.col("val").gt(10)))
    rel = dag.ref("filtered").filter(ma.col("val").gt(20))
    df = _to_eager(dag.execute(rel))
    assert df["id"].to_list() == [3]


def test_execute_no_refs():
    """Execute a relation with no RefRelNodes (inline data)."""
    dag = RelationDAG()
    dag.add("unused", ma.relation([{"x": 1}]))
    rel = ma.relation([{"a": 10, "b": 20}]).filter(ma.col("a").gt(5))
    df = _to_eager(dag.execute(rel))
    assert df["a"].to_list() == [10]


def test_execute_missing_ref():
    """Referencing a name not in the DAG raises KeyError."""
    dag = RelationDAG()
    rel = dag.ref("nonexistent").filter(ma.col("x").gt(0))
    with pytest.raises(KeyError, match="nonexistent"):
        dag.execute(rel)


def test_execute_does_not_mutate_dag():
    """execute() must not add relations or edges to the DAG."""
    dag = RelationDAG()
    dag.add("src", ma.relation([{"x": 1}]))
    relations_before = dict(dag.relations)
    edges_before = set(dag.dependency_edges)

    rel = dag.ref("src").filter(ma.col("x").gt(0))
    dag.execute(rel)

    assert dag.relations == relations_before
    assert dag.dependency_edges == edges_before


def test_execute_matches_collect():
    """execute() and collect() produce identical results for the same relation."""
    dag = RelationDAG()
    dag.add("data", ma.relation([
        {"id": 1, "val": 10},
        {"id": 2, "val": 20},
    ]))

    rel = dag.ref("data").filter(ma.col("val").gt(15))

    # Via execute (ad-hoc)
    df_execute = _to_eager(dag.execute(rel))

    # Via collect (registered)
    dag.add("query", dag.ref("data").filter(ma.col("val").gt(15)))
    df_collect = _to_eager(dag.collect("query"))

    assert df_execute["id"].to_list() == df_collect["id"].to_list() == [2]
