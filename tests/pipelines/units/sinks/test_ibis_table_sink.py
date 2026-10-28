# tests/pipelines/units/sinks/test_ibis_table_sink.py — dialect × mode × key shape × self-dependent input
import pathlib
import pytest, ibis, polars as pl
import mountainash as ma
from mountainash.pipelines.core.values import *
from mountainash.pipelines.units.sinks.base import WriteMode
from mountainash.pipelines.units.sinks.ibis_table import IbisTableSink
from mountainash.pipelines.errors import AmbiguousWrite

import os
DIALECTS = ["duckdb", "sqlite", "postgres"]

@pytest.fixture(params=DIALECTS)
def con(request, tmp_path):
    if request.param == "duckdb": yield ibis.duckdb.connect(); return
    if request.param == "sqlite": yield ibis.sqlite.connect(tmp_path / "t.db"); return
    url = os.environ.get("MA_PG_URL")
    if not url: pytest.skip("blocked: MA_PG_URL unset — PostgreSQL sink cells not qualified in this environment")
    c = ibis.connect(url); yield c                                   # URL-aware entry point (F29)
    for t in c.list_tables():
        if t.startswith(("t", "_ma_")): c.drop_table(t, force=True)

def _ctx(): return RunContext({}, None, {}, "p", "k", "r")
def _rows(*t): return [{"id": i, "p": p, "v": v} for i, p, v in t]

@pytest.mark.parametrize("mode", [WriteMode.APPEND, WriteMode.UPSERT, WriteMode.REPLACE_PARTITION, WriteMode.REPLACE])
@pytest.mark.parametrize("composite", [False, True])
def test_modes_from_records(con, mode, composite):
    keys = ("id", "p") if composite else ("id",); parts = ("p", "q") if composite else ("p",)
    def R(*t): return [{"id": i, "p": p, "q": q, "v": v} for i, p, q, v in t]
    part = (lambda p, q: (p, q)) if composite else (lambda p, q: p)
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=mode, keys=keys, partition_columns=parts)
    first = {part("a", "x"), part("b", "x"), part("a", "y")}
    k.run({"s": Value.of(R((1, "a", "x", 1), (2, "b", "x", 1), (3, "a", "y", 1)), Identity.of("i"), Coverage.source(first, first, set()))}, _ctx())
    k.run({"s": Value.of(R((1, "a", "x", 9)), Identity.of("i"), Coverage.source({part("a", "x")}, {part("a", "x")}, set()))}, _ctx())
    got = {(r["id"], r["p"], r["q"]): r["v"] for r in con.table("t").to_pyarrow().to_pylist()}
    if mode is WriteMode.APPEND: assert con.table("t").count().execute() == 4
    elif mode is WriteMode.UPSERT: assert got == {(1, "a", "x"): 9, (2, "b", "x"): 1, (3, "a", "y"): 1}
    elif mode is WriteMode.REPLACE: assert got == {(1, "a", "x"): 9}
    else:   # REPLACE_PARTITION: composite replaces only (a,x) and keeps (a,y); single-column replaces all p=a
        assert got == ({(1, "a", "x"): 9, (2, "b", "x"): 1, (3, "a", "y"): 1} if composite else {(1, "a", "x"): 9, (2, "b", "x"): 1})

def test_replace_partition_inserts_only_succeeded_rows(con):                    # F19
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p",))
    k.run({"s": Value.of(_rows((1, "a", 1), (2, "b", 1)), Identity.of("i"), Coverage.source({"a", "b"}, {"a"}, {"b"}))}, _ctx())
    assert {r["p"] for r in con.table("t").to_pyarrow().to_pylist()} == {"a"}       # failed partition never touched, even on first create

def test_replace_partition_with_no_successes_creates_empty_destination(con):    # F37
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p",))
    ref = k.run({"s": Value.of(_rows((1, "a", 1)), Identity.of("i"), Coverage.source({"a"}, set(), {"a"}))}, _ctx())
    assert k.reference_exists(ref) and ref.record_count == 0 and set(con.table("t").columns) == {"id", "p", "v"}

def test_sink_identity_includes_destination_and_mode(con):                      # F17
    a = IbisTableSink(con, "t1", name="k", depends_on=("s",), mode=WriteMode.APPEND).identity({"s": Identity.of("u")}, {}, None)
    b = IbisTableSink(con, "t2", name="k", depends_on=("s",), mode=WriteMode.APPEND).identity({"s": Identity.of("u")}, {}, None)
    c = IbisTableSink(con, "t1", name="k", depends_on=("s",), mode=WriteMode.UPSERT, keys=("id",)).identity({"s": Identity.of("u")}, {}, None)
    assert len({a, b, c}) == 3

def test_reference_exists_is_destination_owned(con):                              # F16
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND)
    ref = k.run({"s": Value.of(_rows((1, "a", 1)), Identity.of("i"))}, _ctx())
    assert ref.locator.endswith("/t") and k.reference_exists(ref)
    con.drop_table("t"); assert not k.reference_exists(ref)

def test_destination_distinguishes_databases(tmp_path):                            # F6/F17
    a = ibis.sqlite.connect(tmp_path / "a.db"); b = ibis.sqlite.connect(tmp_path / "b.db")
    ka = IbisTableSink(a, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND); kb = IbisTableSink(b, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND)
    assert ka.destination() != kb.destination() and ka.identity({"s": Identity.of("u")}, {}, None) != kb.identity({"s": Identity.of("u")}, {}, None)
    (tmp_path / "p").mkdir(); (tmp_path / "q").mkdir()
    d1 = ibis.duckdb.connect(tmp_path / "p" / "x.duckdb"); d1b = ibis.duckdb.connect(tmp_path / "q" / "x.duckdb"); d2 = ibis.duckdb.connect(); d2b = ibis.duckdb.connect()
    dest = lambda c: IbisTableSink(c, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND).destination()   # noqa: E731
    assert len({dest(d1), dest(d1b), dest(d2), dest(d2b)}) == 4                   # same catalog name, different files; two in-memory dbs are distinct
    m1 = ibis.sqlite.connect(); m2 = ibis.sqlite.connect()
    assert dest(m1) != dest(m2) and dest(m1) == dest(m1)                          # two live in-memory dbs differ; stable for one connection
    seen = set()
    for _ in range(20):                                                           # successive short-lived connections never collide (no id() recycling)
        c = ibis.sqlite.connect(); seen.add(dest(c)); del c
    assert len(seen) == 20
    d2.raw_sql("CREATE SCHEMA s2"); d3 = ibis.duckdb.connect(); 
    before = IbisTableSink(d2, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND).destination()
    d2.raw_sql("SET schema 's2'")
    assert IbisTableSink(d2, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND).destination() != before     # active schema is part of identity (F40)

def test_completed_append_is_reused_after_a_real_process_restart(tmp_path):     # F16 end to end
    import subprocess, sys, textwrap
    script = textwrap.dedent(f"""
        import sys; sys.path.insert(0, {str(pathlib.Path(__file__).parents[3])!r})
        import ibis
        from mountainash.pipelines.core.pipeline import Pipeline
        from mountainash.pipelines.core.values import *
        from mountainash.pipelines.runtime.checkpoint import FileCheckpoint
        from mountainash.pipelines.runtime.runner import Runner
        from mountainash.pipelines.units.python import PythonUnit
        from mountainash.pipelines.units.source import CallableSource
        from mountainash.pipelines.units.sinks.base import WriteMode
        from mountainash.pipelines.units.sinks.ibis_table import IbisTableSink
        con = ibis.sqlite.connect({str(tmp_path / 'db.sqlite')!r})
        def fetch(up, params, state): return SourceResult(Value.of([{{"id": 1, "p": "a", "v": 1}}], Identity.of("t"), Coverage.source({{"a"}}, {{"a"}}, set())), "a")
        FAIL = sys.argv[1] == "1"
        fail = PythonUnit(lambda r, ctx: (_ for _ in ()).throw(RuntimeError("Y down")) if FAIL else r, name="Y", depends_on=("S",))
        p = Pipeline("r").add(CallableSource(fetch, name="S")).add(IbisTableSink(con, "t", name="X", depends_on=("S",), mode=WriteMode.APPEND)).add(fail)
        r = Runner(p, checkpoint=FileCheckpoint({str(tmp_path / 'cp')!r})).run()
        print(r.statuses["X"].value, int(con.table("t").count().execute()))
    """)
    def run(fail):
        return subprocess.run([sys.executable, "-c", script, "1" if fail else "0"], capture_output=True, text=True, check=True).stdout.split()
    assert run(True) == ["complete", "1"]                      # X appended once, Y failed → S pending
    assert run(False) == ["reused", "1"]                       # fresh process: X REUSED via destination-owned liveness; no duplicate row

def test_foreign_connection_input_exports_once_then_imports(con):
    from unittest import mock
    from mountainash.relations.backends.relation_systems.ibis.base import IbisBaseRelationSystem
    other = ibis.duckdb.connect(); other.create_table("src", pl.DataFrame({"id": [1], "p": ["a"], "v": [1]}).to_arrow())
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND)
    with mock.patch.object(IbisBaseRelationSystem, "export", wraps=IbisBaseRelationSystem.export, autospec=True) as spy:
        k.run({"s": Value.of(other.table("src"), Identity.of("i"))}, _ctx())
    assert spy.call_count == 1 and con.table("t").count().execute() == 1

def test_same_connection_native_write_zero_exports(con):
    from unittest import mock
    from mountainash.relations.backends.relation_systems.ibis.base import IbisBaseRelationSystem
    con.create_table("src", pl.DataFrame({"id": [1, 2], "p": ["a", "a"], "v": [1, 2]}).to_arrow())
    expr = con.table("src").filter(ibis._.v > 1)
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.UPSERT, keys=("id",))
    with mock.patch.object(IbisBaseRelationSystem, "export", side_effect=AssertionError("export")):
        ref = k.run({"s": Value.of(expr, Identity.of("i"))}, _ctx())
    assert ref.record_count == 1 and k.reference_exists(ref)

@pytest.mark.parametrize("mode", [WriteMode.UPSERT, WriteMode.REPLACE_PARTITION, WriteMode.REPLACE, WriteMode.APPEND])
@pytest.mark.parametrize("composite", [False, True])
def test_self_dependent_input_every_mode(con, mode, composite):                  # full product: mode × shape × self-dependent
    con.create_table("t", pl.DataFrame({"id": [1, 2], "p": ["a", "a"], "q": ["x", "y"], "v": [1, 2]}).to_arrow())
    expr = con.table("t").mutate(v=ibis._.v * 10)
    keys = ("id", "p") if composite else ("id",); parts = ("p", "q") if composite else ("p",)
    cov = Coverage.source({("a", "x"), ("a", "y")} if composite else {"a"}, {("a", "x"), ("a", "y")} if composite else {"a"}, set())
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=mode, keys=keys, partition_columns=parts)
    k.run({"s": Value.of(expr, Identity.of("i"), cov)}, _ctx())
    vs = sorted(r["v"] for r in con.table("t").to_pyarrow().to_pylist())
    assert vs == ([1, 2, 10, 20] if mode is WriteMode.APPEND else [10, 20])

def test_recovery_contract_with_real_upsert_sink(con, tmp_path):                 # §8 two-run contract end to end with IbisTableSink
    from pathlib import Path
    from mountainash.pipelines.core.pipeline import Pipeline
    from mountainash.pipelines.runtime.checkpoint import FileCheckpoint
    from mountainash.pipelines.runtime.runner import Runner
    from mountainash.pipelines.units.source import CallableSource
    calls = []
    def fetch(up, params, state):
        calls.append(state)
        if len(calls) == 1: return SourceResult(Value.of(_rows((2, "b", 1)), Identity.of("t"), Coverage.source({"a", "b"}, {"b"}, {"a"})), None)
        return SourceResult(Value.of(_rows((1, "a", 1)), Identity.of("t"), Coverage.source({"a"}, {"a"}, set())), "a")
    p = Pipeline("r").add(CallableSource(fetch, name="S")).add(IbisTableSink(con, "t", name="K", depends_on=("S",), mode=WriteMode.UPSERT, keys=("id",)))
    Runner(p, checkpoint=FileCheckpoint(tmp_path / "cp")).run(); Runner(p, checkpoint=FileCheckpoint(tmp_path / "cp")).run()
    assert {r["p"] for r in con.table("t").to_pyarrow().to_pylist()} == {"a", "b"} and FileCheckpoint(tmp_path / "cp").progress("S").cursor == "a"

def test_interrupted_and_two_sink_contracts_with_real_sinks(con, tmp_path):     # §8 interrupted + partial-plus-two-sinks on IbisTableSink
    from mountainash.pipelines.core.pipeline import Pipeline
    from mountainash.pipelines.runtime.checkpoint import FileCheckpoint
    from mountainash.pipelines.runtime.runner import Runner
    from mountainash.pipelines.units.python import PythonUnit
    from mountainash.pipelines.units.source import CallableSource
    calls = []
    def fetch(up, params, state):
        calls.append(state)
        if len(calls) == 1: return SourceResult(Value.of(_rows((2, "b", 1)), Identity.of("t"), Coverage.source({"a", "b"}, {"b"}, {"a"})), None)
        return SourceResult(Value.of(_rows((1, "a", 1)), Identity.of("t"), Coverage.source({"a"}, {"a"}, set())), "a")
    flaky = {"n": 0}
    def y_fn(rows_, ctx):
        flaky["n"] += 1
        if flaky["n"] == 1: raise RuntimeError("Y down")
        return rows_
    p = (Pipeline("r").add(CallableSource(fetch, name="S"))
         .add(IbisTableSink(con, "tx", name="X", depends_on=("S",), mode=WriteMode.UPSERT, keys=("id",)))
         .add(PythonUnit(y_fn, name="Yg", depends_on=("S",)))
         .add(IbisTableSink(con, "ty", name="Y", depends_on=("Yg",), mode=WriteMode.UPSERT, keys=("id",))))
    Runner(p, checkpoint=FileCheckpoint(tmp_path / "cp")).run()                 # X wrote B; Y failed → attempt pending
    assert FileCheckpoint(tmp_path / "cp").pending("S") is not None and FileCheckpoint(tmp_path / "cp").progress("S") == SourceState()
    r2 = Runner(p, checkpoint=FileCheckpoint(tmp_path / "cp")).run()            # replay: X REUSED, Y gets the same B
    assert r2.statuses["X"] is Status.REUSED and r2.statuses["Y"] is Status.COMPLETE and len(calls) == 1
    assert con.table("tx").count().execute() == 1 and con.table("ty").count().execute() == 1
    assert FileCheckpoint(tmp_path / "cp").progress("S") == SourceState(None, frozenset({"a"}), frozenset({"b"})) and FileCheckpoint(tmp_path / "cp").pending("S") is None
    Runner(p, checkpoint=FileCheckpoint(tmp_path / "cp")).run()                 # fresh attempt fetches A
    assert calls[1] == SourceState(None, frozenset({"a"}), frozenset({"b"}))
    assert {r["p"] for r in con.table("tx").to_pyarrow().to_pylist()} == {"a", "b"} == {r["p"] for r in con.table("ty").to_pyarrow().to_pylist()}
    assert FileCheckpoint(tmp_path / "cp").progress("S").cursor == "a"

def test_partial_source_through_dag_unit_refuses_replace_and_preserved_chain_allows_partition(con, tmp_path):
    import mountainash as ma
    from mountainash.relations.dag import RelationDAG
    from mountainash.pipelines.core.pipeline import Pipeline
    from mountainash.pipelines.runtime.runner import Runner
    from mountainash.pipelines.units.dag import DagUnit
    from mountainash.pipelines.units.python import PythonUnit
    from mountainash.pipelines.units.source import CallableSource
    def fetch(up, params, state): return SourceResult(Value.of(_rows((1, "a", 1)), Identity.of("t"), Coverage.source({"a", "b"}, {"a"}, {"b"})), None)
    t = RelationDAG(); t.add("out", t.ref("src").select("id", "p", "v"))
    p = Pipeline("c").add(CallableSource(fetch, name="S")).add(DagUnit(t, "out", name="D", inputs={"S": "src"})).add(IbisTableSink(con, "t", name="K", depends_on=("D",), mode=WriteMode.REPLACE))
    assert Runner(p).run().statuses["K"] is Status.FAILED                               # IncompleteCoverage through the DagUnit marker
    q = Pipeline("d").add(CallableSource(fetch, name="S")).add(PythonUnit(lambda r, ctx: r, name="T", depends_on=("S",), partitions_preserved=True)).add(IbisTableSink(con, "t2", name="K", depends_on=("T",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p",)))
    assert Runner(q).run().statuses["K"] is Status.COMPLETE

def test_self_dependent_replace_partition_preserves_rows(con):
    con.create_table("t", pl.DataFrame({"id": [1, 2], "p": ["a", "a"], "v": [1, 2]}).to_arrow())
    expr = con.table("t").mutate(v=ibis._.v * 10)            # reads the destination
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p",))
    k.run({"s": Value.of(expr, Identity.of("i"), Coverage.source({"a"}, {"a"}, set()))}, _ctx())
    assert sorted(r["v"] for r in con.table("t").to_pyarrow().to_pylist()) == [10, 20]

@pytest.mark.parametrize("failing", ["_count", "_cleanup"])
def test_append_ambiguous_post_write_failure_is_non_retryable(con, monkeypatch, failing):      # F20
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND)
    k.run({"s": Value.of(_rows((1, "a", 1)), Identity.of("i"))}, _ctx())                     # table exists → second write stages
    monkeypatch.setattr(k, failing, lambda *a: (_ for _ in ()).throw(RuntimeError("lost connection")))
    with pytest.raises(AmbiguousWrite):
        k.run({"s": Value.of(_rows((2, "a", 1)), Identity.of("i"))}, _ctx())
    k2 = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.APPEND, allow_duplicate=True)
    monkeypatch.setattr(k2, failing, lambda *a: (_ for _ in ()).throw(RuntimeError("lost connection")))
    with pytest.raises(RuntimeError):                                                            # ordinary, retryable
        k2.run({"s": Value.of(_rows((3, "a", 1)), Identity.of("i"))}, _ctx())

def test_transaction_rolls_back_on_insert_failure(con, monkeypatch):
    k = IbisTableSink(con, "t", name="k", depends_on=("s",), mode=WriteMode.REPLACE)
    k.run({"s": Value.of(_rows((1, "a", 1)), Identity.of("i"))}, _ctx())
    orig = k._tx_exec
    def bad(sql):
        if sql.startswith("INSERT"): raise RuntimeError("disk full")
        return orig(sql)
    monkeypatch.setattr(k, "_tx_exec", bad)
    with pytest.raises(RuntimeError): k.run({"s": Value.of(_rows((2, "a", 2)), Identity.of("i"))}, _ctx())
    assert con.table("t").count().execute() == 1                                              # DELETE rolled back
