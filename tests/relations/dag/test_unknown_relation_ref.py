"""UnknownRelationRef — typed collect-time error for missing upstream refs."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag import RelationDAG, UnknownRelationRef


def test_collect_missing_upstream_raises_typed_error():
    dag = RelationDAG()
    dag.add("derived", dag.ref("missing"))
    with pytest.raises(UnknownRelationRef, match="'missing'.*'derived'"):
        dag.collect("derived")


def test_execute_missing_ref_raises_typed_error():
    dag = RelationDAG()
    with pytest.raises(UnknownRelationRef, match="'missing'.*unregistered"):
        dag.execute(dag.ref("missing"))


def test_unknown_relation_ref_is_keyerror_compatible():
    # Builtin-compat via MI: pre-existing `except KeyError` sites keep working.
    dag = RelationDAG()
    dag.add("derived", dag.ref("missing"))
    with pytest.raises(KeyError):
        dag.collect("derived")


def test_error_message_renders_without_keyerror_quotes():
    # KeyError.__str__ would repr() the message (spurious outer quotes); the
    # error overrides __str__ so tracebacks/logs read the plain sentence.
    dag = RelationDAG()
    dag.add("derived", dag.ref("missing"))
    with pytest.raises(UnknownRelationRef) as excinfo:
        dag.collect("derived")
    assert str(excinfo.value) == (
        "relation 'missing' referenced but not in DAG (referenced by 'derived')"
    )


def test_registration_stays_order_independent():
    # add() stays permissive: registering the derived relation first is legal,
    # and collect succeeds once the upstream arrives.
    dag = RelationDAG()
    dag.add("derived", dag.ref("raw"))
    dag.add("raw", ma.relation(pl.DataFrame({"x": [1, 2]})))
    out = dag.collect("derived")
    assert out.collect().to_dicts() == [{"x": 1}, {"x": 2}]
