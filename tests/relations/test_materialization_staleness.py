"""Repeated real internal terminals must observe fresh source revisions."""
from __future__ import annotations

import ibis
import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import REGISTRY
from mountainash.relations.backends.relation_systems.ibis._physical import adopt_connection, owned_transaction
from mountainash.core.capabilities.policy import CapabilityPolicy, _new_execution_context
from mountainash.core.types import BackendCapabilityError
from mountainash.relations.core.materialization import MaterializationScope
from mountainash.validation.prepared import prepare_validation_input

pytest_plugins = ("fixtures.ibis_physical",)


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-sqlite", "ibis-polars"])
def test_dag_reexecution_is_fresh_while_previous_result_is_alive(backend_name):
    source = REGISTRY[backend_name].build({"x": [7]}, "fresh_source")
    connection = source._find_backend(use_default=False)
    dag = ma.RelationDAG()
    dag.add("source", ma.relation(source).filter(ma.col("x") > 0))
    first = dag.collect("source")
    if connection.name == "polars":
        connection.create_table("fresh_source", pl.DataFrame({"x": [88]}), overwrite=True)
    else:
        with adopt_connection(connection) as backend:
            with owned_transaction(backend):
                backend.drop_table("fresh_source")
                backend.create_table("fresh_source", ibis.memtable({"x": [88]}))
    second = dag.collect("source")
    assert ma.relation(first).to_dicts() == [{"x": 7}]
    assert ma.relation(second).to_dicts() == [{"x": 88}]


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-sqlite", "ibis-polars"])
def test_validation_reexecution_is_fresh_with_prior_scope_open(backend_name):
    source = REGISTRY[backend_name].build({"x": [7]}, "fresh_validation")
    con = source._find_backend(use_default=False)
    context = _new_execution_context(source, policy=CapabilityPolicy.trusted())
    with MaterializationScope() as first_scope, MaterializationScope() as second_scope:
        first = prepare_validation_input(ma.relation(source), scope=first_scope, execution_context=context)
        if con.name == "polars":
            con.create_table("fresh_validation", pl.DataFrame({"x": [88]}), overwrite=True)
        else:
            with adopt_connection(con) as backend:
                with owned_transaction(backend):
                    backend.drop_table("fresh_validation")
                    backend.create_table("fresh_validation", ibis.memtable({"x": [88]}))
        second = prepare_validation_input(ma.relation(source), scope=second_scope, execution_context=context)
        assert first.relation.to_dicts() == [{"x": 7}]
        assert second.relation.to_dicts() == [{"x": 88}]


@pytest.mark.parametrize("owner", ["dag", "validation"])
def test_internal_copy_refuses_caller_transaction_but_collect_passes(connection, owner):
    with adopt_connection(connection) as backend:
        with owned_transaction(backend):
            backend.create_table("source", ibis.memtable({"x": [7]}), temp=True)
            source = backend.table("source")
        before = None
        with owned_transaction(backend):
            before = set(backend.list_tables())
        rel = ma.relation(source).filter(ma.col("x") > 0)
        dag = ma.RelationDAG()
        dag.add("source", rel)
        with backend.transaction(required=True):
            with pytest.raises(BackendCapabilityError):
                if owner == "dag":
                    dag.collect("source")
                else:
                    with MaterializationScope() as scope:
                        prepare_validation_input(rel, scope=scope, execution_context=_new_execution_context(
                            source, policy=CapabilityPolicy.trusted()))
            assert backend.native_transaction_open() is True
            # Ordinary collect builds a deferred expression without a copy.
            assert isinstance(rel.collect(), ibis.expr.types.Table)
        with owned_transaction(backend):
            assert set(backend.list_tables()) == before
            assert backend.run_expr(source)["x"].tolist() == [7]
