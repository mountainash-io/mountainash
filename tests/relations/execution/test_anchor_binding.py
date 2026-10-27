"""Anchor planning: which transfer into a bound Ibis root becomes the owned table."""

import ibis
import polars as pl
import pytest

import mountainash as ma
from mountainash import RelationDAG
from mountainash.relations.core.errors import CompileRequiresExecutionError, UnresolvedExecutionLocationError
from mountainash.relations.core.execution.preparation import ExecutionPhase, prepare_execution

SRC = pl.DataFrame({"id": [1, 2, 3], "v": [10, None, 30]})


def prep(rel, target):
    return prepare_execution(rel._node, phase=ExecutionPhase.EXECUTE, target=target)


def owned_keys(p):
    return [k for k, r in p.transfers.items() if r.owned]


def test_derived_in_memory_dag_on_connection():
    con = ibis.duckdb.connect()
    dag = RelationDAG()
    dag.add("t", ma.relation(SRC))
    dag.add("u", dag.ref("t").filter(ma.col("id").gt(1)))
    out = dag.collect("u", target=con)
    assert out.get_backend() is con
    assert out.to_polars().sort("id").to_dicts() == [{"id": 2, "v": None}, {"id": 3, "v": 30}]


def test_union_of_two_in_memory_inputs_anchor_is_input_zero():
    con = ibis.duckdb.connect()
    r = ma.concat([ma.relation(SRC), ma.relation(pl.DataFrame({"id": [4], "v": [40]}))])
    assert owned_keys(prep(r, con)) == ["root/inputs/0"]
    assert sorted(d["id"] for d in r.collect(target=con).to_polars().to_dicts()) == [1, 2, 3, 4]


def test_surviving_native_anchor_no_owned():
    con = ibis.duckdb.connect()
    bound = con.create_table("base", {"id": [1, 2, 3]})
    assert owned_keys(prep(ma.relation(bound).join(ma.relation(SRC), on="id"), con)) == []


def test_early_operand_then_surviving_anchor():
    con = ibis.duckdb.connect()
    bound = con.create_table("base", {"id": [1, 2, 3]})
    rel = ma.relation(SRC).join(ma.relation(bound), on="id", execute_on="right")
    assert owned_keys(prep(rel, con)) == []
    assert rel.collect(target=con).get_backend() is con


def test_nested_b_a_b_anchor_at_root_input():
    A, B = ibis.duckdb.connect(), ibis.duckdb.connect()
    ta = A.create_table("ta", {"id": [1, 2], "x": [1, 2]})
    tb = B.create_table("tb", {"id": [1, 2]})
    rel = ma.relation(ta).join(ma.relation(tb), on="id").filter(ma.col("x").gt(0))
    assert owned_keys(prep(rel, B)) == ["root/input"]
    assert rel.collect(target=B).get_backend() is B


def test_borrowed_memory_graph_gets_one_owned_anchor():
    con = ibis.duckdb.connect()
    rel = ma.relation(ibis.memtable(SRC.to_arrow())).filter(ma.col("id").gt(0))
    assert owned_keys(prep(rel, con)) == ["root/input"]
    assert rel.collect(target=con).get_backend() is con


def test_retargeted_native_read_root():
    con = ibis.duckdb.connect()
    assert owned_keys(prep(ma.relation(SRC), con)) == ["root"]
    assert ma.relation(SRC).collect(target=con).get_backend() is con


def test_ref_dependency_on_connection():
    con = ibis.duckdb.connect()
    dag = RelationDAG()
    dag.add("t", ma.relation(SRC))
    assert dag.execute(dag.ref("t").filter(ma.col("id").gt(1)), target=con).get_backend() is con


def test_memtable_only_family_target_unresolved():
    with pytest.raises(UnresolvedExecutionLocationError):
        ma.relation(ibis.memtable(SRC.to_arrow())).filter(ma.col("id").gt(0)).collect(target="ibis")


def test_compile_rejects_owned_anchor_without_import(monkeypatch):
    import mountainash.relations.core.owned_copy as oc

    monkeypatch.setattr(oc, "owned_arrow_table", lambda *a, **k: pytest.fail("imported during compile"))
    with pytest.raises(CompileRequiresExecutionError):
        prepare_execution(ma.relation(SRC).filter(ma.col("id").gt(1))._node,
                          phase=ExecutionPhase.COMPILE, target=ibis.duckdb.connect())


@pytest.mark.parametrize("build", [
    lambda b: ma.relation(pl.DataFrame({"id": [1]})).join(ma.relation(ibis.memtable({"id": [1], "x": [2]})), on="id"),
    lambda b: ma.relation(b).join(ma.relation(ibis.memtable({"id": [1], "x": [2]}).filter(ibis._.x > 0)), on="id"),
    lambda b: ma.relation(b).join({"id": [1], "z": [9]}, on="id"),
])
def test_baseline_compile_safe_cases_still_compile(build):
    con = ibis.duckdb.connect()
    b = con.create_table("b", {"id": [1]})
    before = con.list_tables()
    build(b).compile()
    assert con.list_tables() == before


def test_separate_collects_create_separate_anchors():
    con = ibis.duckdb.connect()
    dag = RelationDAG()
    dag.add("t", ma.relation(SRC))
    a, b = dag.collect("t", target=con), dag.collect("t", target=con)
    assert a.op() is not b.op()
    assert a.to_polars().equals(b.to_polars())


def test_unprepared_validation_join_still_coerces():
    import pandas as pd

    dag = RelationDAG()
    dag.add("l", ma.relation(pl.DataFrame({"id": [1, 2]})))
    dag.add("r", ma.relation(pd.DataFrame({"id": [2]})))
    dag.add("j", dag.ref("l").join(dag.ref("r"), on="id"))
    from mountainash.core.capabilities.policy import _resolve_policy
    from mountainash.relations.dag.materialization import DAGMaterializationSession

    session = DAGMaterializationSession(dag, execution_policy=_resolve_policy())
    try:
        native, _visitor = session.compile_registered("j")
        assert native.value is not None
    finally:
        session.close(release_owned=True)


def test_derived_polars_dag_to_narwhals():
    dag = RelationDAG()
    dag.add("t", ma.relation(pl.DataFrame({"id": [1, 2, 3]})))
    dag.add("u", dag.ref("t").filter(ma.col("id").gt(1)))
    out = dag.collect("u", target="narwhals")
    assert str(out.implementation).lower().endswith("polars")
    assert out.to_native().to_dicts() == [{"id": 2}, {"id": 3}]


def test_egress_moves_compiled_root_to_requested_location():
    from mountainash.relations.core.execution.compilation import CompilationSession
    from mountainash.relations.core.execution.location import LocationResolver

    prepared = prepare_execution(
        ma.relation(SRC).filter(ma.col("id").gt(1))._node, phase=ExecutionPhase.EXECUTE,
    )
    session = CompilationSession(prepared)
    try:
        out = session.egress(LocationResolver(prepared.tokens).resolve_target("narwhals-pandas"))
        assert str(out.implementation).lower().endswith("pandas")
        assert out.to_native()["id"].tolist() == [2, 3]
    finally:
        session.close(release_owned=False)


def _derived_memory_dag():
    dag = RelationDAG()
    dag.add("t", ma.relation(ibis.memtable(SRC.to_arrow())).filter(ma.col("id").gt(1)))
    return dag


def test_borrowed_anchor_under_ref_is_consumed_by_the_named_compilation():
    con = ibis.duckdb.connect()
    dag = _derived_memory_dag()
    out = dag.execute(dag.ref("t"), target=con)
    assert out.get_backend() is con
    assert len(con.list_tables()) == 1
    assert out.to_polars().sort("id").to_dicts() == [{"id": 2, "v": None}, {"id": 3, "v": 30}]


def test_borrowed_anchor_under_nested_alias_is_consumed():
    con = ibis.duckdb.connect()
    dag = _derived_memory_dag()
    dag.add("alias", dag.ref("t"))
    out = dag.execute(dag.ref("alias"), target=con)
    assert out.get_backend() is con
    assert len(con.list_tables()) == 1
    assert out.to_polars().sort("id")["id"].to_list() == [2, 3]


def test_registered_native_read_with_session_target_is_moved_before_publication():
    from mountainash.core.capabilities.policy import _resolve_policy
    from mountainash.relations.dag.materialization import DAGMaterializationSession

    dag = RelationDAG()
    dag.add("p", ma.relation(SRC))
    session = DAGMaterializationSession(dag, execution_policy=_resolve_policy(), target="narwhals")
    try:
        native, _visitor = session.compile_registered("p")
        assert str(native.value.implementation).lower().endswith("polars")
        assert type(native.value).__module__.startswith("narwhals")
        assert native.value_identity.family.value == "narwhals"
    finally:
        session.close(release_owned=True)
