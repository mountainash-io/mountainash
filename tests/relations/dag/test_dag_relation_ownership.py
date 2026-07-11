"""DAG-ownership guards on combining builders. PR-2 §2.2."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag import DAGRelation
from mountainash.relations.core.relation_api.relation import concat


def _two_dags():
    d1 = RelationDAG()
    d2 = RelationDAG()
    a = d1.source("a", pl.DataFrame({"k": [1], "v": [1]}))
    b = d2.source("b", pl.DataFrame({"k": [1], "w": [2]}))
    return d1, d2, a, b


def test_join_across_different_dags_raises():
    _, _, a, b = _two_dags()
    with pytest.raises(ValueError, match="different DAG"):
        a.join(b, on="k")


def test_join_same_dag_ok_and_preserves_type():
    d1 = RelationDAG()
    a = d1.source("a", pl.DataFrame({"k": [1], "v": [1]}))
    b = d1.source("b", pl.DataFrame({"k": [1], "w": [2]}))
    joined = a.join(b, on="k")
    assert isinstance(joined, DAGRelation)


def test_join_plain_relation_operand_ok():
    d1 = RelationDAG()
    a = d1.source("a", pl.DataFrame({"k": [1], "v": [1]}))
    plain = ma.relation(pl.DataFrame({"k": [1], "w": [2]}))
    assert isinstance(a.join(plain, on="k"), DAGRelation)


def test_join_reverse_order_propagates_dag_ownership():
    # DAG operand on the RIGHT: plain.join(dag.ref(...)). _to_relation_node
    # unwraps it, so ownership must be resolved from the ORIGINAL operands in
    # the base combiner, not from the unwrapped node.
    d1 = RelationDAG()
    d1.add("b", ma.relation(pl.DataFrame({"k": [1], "w": [2]})))
    plain = ma.relation(pl.DataFrame({"k": [1], "v": [1]}))
    joined = plain.join(d1.ref("b"), on="k")
    assert isinstance(joined, DAGRelation)
    # and it compiles through the DAG (no RelationDAGRequired)
    assert joined.count_rows() == 1


def test_concat_same_dag_returns_dagrelation():
    d1 = RelationDAG()
    a = d1.source("a", pl.DataFrame({"x": [1]}))
    b = d1.source("b", pl.DataFrame({"x": [2]}))
    assert isinstance(concat([a, b]), DAGRelation)


def test_concat_mixed_dags_raises():
    _, _, a, b = _two_dags()
    with pytest.raises(ValueError, match="different DAG"):
        concat([a, b])


def test_concat_dag_plus_plain_returns_dagrelation():
    d1 = RelationDAG()
    a = d1.source("a", pl.DataFrame({"x": [1]}))
    plain = ma.relation(pl.DataFrame({"x": [2]}))
    assert isinstance(concat([a, plain]), DAGRelation)


def test_join_asof_cross_dag_raises():
    # join_asof must guard too (same _combine_result path).
    d1 = RelationDAG()
    d2 = RelationDAG()
    a = d1.source("a", pl.DataFrame({"t": [1], "v": [1]}))
    b = d2.source("b", pl.DataFrame({"t": [1], "w": [2]}))
    with pytest.raises(ValueError, match="different DAG"):
        a.join_asof(b, on="t")
