# tests/pipelines/runtime/test_nested.py
import threading
import pytest
from mountainash.pipelines.core.pipeline import Pipeline
from mountainash.pipelines.core.values import *
from mountainash.pipelines.runtime.checkpoint import FileCheckpoint
from mountainash.pipelines.runtime.runner import Runner
from mountainash.pipelines.units.nested import PipelineUnit
from mountainash.pipelines.units.python import PythonUnit
from mountainash.pipelines.units.source import CallableSource
from tests.pipelines.runtime.test_recovery_contracts import LogSink, rows, A

def _src(calls, cursor=A, partial=False):
    def fetch(up, params, state):
        calls.append(state)
        if partial: return SourceResult(Value.of(rows("B"), Identity.of("t"), Coverage.source({A, "B"}, {"B"}, {A})), None)
        return SourceResult(Value.of(rows(cursor), Identity.of("t"), Coverage.source({cursor}, {cursor}, set())), cursor)
    return fetch

def test_nested_outer_sink_failure_keeps_inner_pending_then_replays(tmp_path):
    calls = []
    inner = Pipeline("inner").add(CallableSource(_src(calls), name="S")).add(PythonUnit(lambda r, ctx: r, name="T", depends_on=("S",)))
    outer = Pipeline("outer").add(PipelineUnit(inner, "T", name="N")).add(LogSink("X", "N", fail_times=1))
    Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run()
    cp = FileCheckpoint(tmp_path); assert cp.scoped("N").pending("S") is not None and cp.scoped("N").progress("S").cursor is None
    r = Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run()
    assert len(calls) == 1 and r.statuses["X"] is Status.COMPLETE and FileCheckpoint(tmp_path).scoped("N").progress("S").cursor == A

def test_reused_outer_commits_inner_via_last_status_without_promoting_partial(tmp_path):
    calls = []
    inner = Pipeline("inner").add(CallableSource(_src(calls, partial=True), name="S")).add(PythonUnit(lambda r, ctx: r, name="T", depends_on=("S",)))
    outer = Pipeline("outer").add(PipelineUnit(inner, "T", name="N")).add(LogSink("X", "N", fail_times=1))
    Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run(); Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run()
    cp = FileCheckpoint(tmp_path)
    assert cp.scoped("N").pending("S") is None and cp.scoped("N").progress("S").outstanding == frozenset({A})   # committed as PARTIAL progress via last_status path

def test_regenerate_invalidates_only_inner_descendants_of_source(tmp_path):      # Review Focus #3, F9/F10
    import polars as pl
    s_calls, w_calls, v_seen = [], [], []
    def fetch_s(up, params, state):
        s_calls.append(state); return SourceResult(Value.of(pl.DataFrame({"p": [A]}), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    def fetch_w(up, params, state):
        w_calls.append(state); return SourceResult(Value.of(rows("W"), Identity.of("w"), Coverage.source({"W"}, {"W"}, set())), "W")
    def fetch_v(up, params, state):
        v_seen.append(up["S"].payload); return SourceResult(Value.of(rows("V"), Identity.of("v"), Coverage.source({"V"}, {"V"}, set())), "V")
    inner = (Pipeline("inner", inputs=("S",)).add(CallableSource(fetch_w, name="W")).add(CallableSource(fetch_v, name="V", depends_on=("S",)))
             .add(PythonUnit(lambda w, v, ctx: w + v, name="J", depends_on=("W", "V"))))
    outer = Pipeline("outer").add(CallableSource(fetch_s, name="S")).add(PipelineUnit(inner, "J", name="N", depends_on=("S",))).add(LogSink("X", "N", fail_times=1))
    Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run()          # all inner attempts pending, X failed
    Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run()          # S regenerates (TABULAR not retained) → V retired & refetched; W replayed
    assert len(s_calls) == 2 and len(v_seen) == 2 and len(w_calls) == 1
    cp = FileCheckpoint(tmp_path)
    assert cp.scoped("N").progress("W").cursor == "W" and cp.scoped("N").progress("V").cursor == "V" and cp.progress("S").cursor == A

def test_two_levels_of_nesting_invalidate_recursively(tmp_path):
    import polars as pl
    deep_seen = []
    def fetch_s(up, params, state): return SourceResult(Value.of(pl.DataFrame({"p": [A]}), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    def fetch_d(up, params, state):
        deep_seen.append(1); return SourceResult(Value.of(rows("D"), Identity.of("d"), Coverage.source({"D"}, {"D"}, set())), "D")
    deep = Pipeline("deep", inputs=("S",)).add(CallableSource(fetch_d, name="D", depends_on=("S",)))
    mid = Pipeline("mid", inputs=("S",)).add(PipelineUnit(deep, "D", name="M", depends_on=("S",)))
    outer = Pipeline("outer").add(CallableSource(fetch_s, name="S")).add(PipelineUnit(mid, "M", name="N", depends_on=("S",))).add(LogSink("X", "N", fail_times=1))
    Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run(); Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run()
    assert len(deep_seen) == 2 and FileCheckpoint(tmp_path).scoped("N").scoped("M").progress("D").cursor == "D"

def test_commit_leaves_pending_attempts_outside_target_subgraph_untouched(tmp_path):
    calls = []
    p = Pipeline("t").add(CallableSource(_src(calls), name="S1")).add(CallableSource(_src(calls, cursor="B"), name="S2")).add(LogSink("X", "S1", fail_times=1))
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()                       # both pending (X failed; S2 has no consumer → committed? no: S2 committed, S1 pending)
    before = dict(FileCheckpoint(tmp_path).pending_all())
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run(target="S2")            # S1 outside the selected subgraph
    after = dict(FileCheckpoint(tmp_path).pending_all())
    assert before.get(("S1",)) == after.get(("S1",))

def test_slash_named_source_commits(tmp_path):                                  # F38/P13
    calls = []
    p = Pipeline("t").add(CallableSource(_src(calls), name="tenant/fetch__daily")).add(LogSink("X", "tenant/fetch__daily"))
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert FileCheckpoint(tmp_path).progress("tenant/fetch__daily").cursor == A and FileCheckpoint(tmp_path).pending("tenant/fetch__daily") is None

def test_nested_main_affinity_runs_on_caller_thread():
    seen = {}
    inner = Pipeline("inner").add(PythonUnit(lambda ctx: seen.update({"m": threading.current_thread().name}) or rows(A), name="m", affinity=Affinity.MAIN))
    p = Pipeline("e").add(PythonUnit(lambda ctx: rows(A), name="w1")).add(PipelineUnit(inner, "m", name="N"))
    Runner(p, workers=3).run(force=True)
    assert seen["m"] == threading.current_thread().name

def test_same_runner_nested_force_then_inner_failure_does_not_commit_stale(tmp_path):   # F8, nested
    calls = []
    inner = Pipeline("inner").add(CallableSource(_src(calls), name="S")).add(PythonUnit(lambda r, ctx: r, name="T", depends_on=("S",)))
    t_unit = inner.graph.nodes["T"]
    outer = Pipeline("outer").add(PipelineUnit(inner, "T", name="N"))
    r = Runner(outer, checkpoint=FileCheckpoint(tmp_path)); r.run()
    t_unit.fn = lambda rows_, ctx: (_ for _ in ()).throw(RuntimeError("T down"))
    r.run(force=True)
    assert FileCheckpoint(tmp_path).scoped("N").pending("S") is not None            # run-2 attempt pending; run-1's inner result not reused for commit

def test_inner_failure_fails_outer_and_skips_outer_descendants():
    inner = Pipeline("inner").add(PythonUnit(lambda ctx: (_ for _ in ()).throw(RuntimeError("x")), name="bad"))
    p = Pipeline("e").add(PipelineUnit(inner, "bad", name="N")).add(PythonUnit(lambda n, ctx: n, name="after", depends_on=("N",)))
    r = Runner(p).run()
    assert r.statuses["N"] is Status.FAILED and r.statuses["after"] is Status.SKIPPED


@pytest.mark.parametrize("depth", [1, 2])
def test_nested_regeneration_invalidates_enclosing_runner_descendants(tmp_path, depth):
    import polars as pl
    calls, x_seen, y_seen, y_fail = [], [], [], [1]
    def fetch_s(up, params, state):
        calls.append(state); rev = len(calls)
        return SourceResult(Value.of(pl.DataFrame({"rev": [rev]}), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    def to_records(frame, ctx):
        x_seen.append(frame["rev"][0]); return [{"rev": frame["rev"][0]}]
    def fail_once(recs, ctx):
        y_seen.append(recs[0]["rev"])
        if y_fail: y_fail.pop(); raise RuntimeError("Y down")
        return recs
    deepest = Pipeline("deepest").add(CallableSource(fetch_s, name="S"))
    if depth == 1:
        outer_unit = PipelineUnit(deepest, "S", name="N")
    else:
        mid = Pipeline("mid").add(PipelineUnit(deepest, "S", name="M"))
        outer_unit = PipelineUnit(mid, "M", name="N")
    outer = (Pipeline("outer").add(outer_unit).add(PythonUnit(to_records, name="X", depends_on=("N",)))
             .add(PythonUnit(fail_once, name="Y", depends_on=("X",))))
    r1 = Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run()
    assert r1.statuses["Y"] is Status.FAILED and x_seen == [1] and y_seen == [1]
    r2 = Runner(outer, checkpoint=FileCheckpoint(tmp_path)).run()
    assert len(calls) == 2                                                # S regenerated (frame not retained)
    assert x_seen == [1, 2] and y_seen == [1, 2]                          # X and Y re-ran against revision 2, not REUSED stale data
    assert r2.statuses["X"] is Status.COMPLETE and r2.statuses["Y"] is Status.COMPLETE
    assert r2.values["Y"].payload == [{"rev": 2}]
    cp = FileCheckpoint(tmp_path).scoped("N")
    if depth == 2: cp = cp.scoped("M")
    assert cp.progress("S").cursor == A and cp.pending("S") is None


def test_outer_reuse_checks_inner_sink_destination(tmp_path):            # F32/P8
    from mountainash.pipelines.units.sinks.base import WriteMode
    from mountainash.pipelines.units.sinks.parquet_dir import ParquetDirectorySink
    import polars as pl
    inner = Pipeline("inner").add(PythonUnit(lambda ctx: pl.DataFrame({"a": [1]}), name="src")).add(ParquetDirectorySink(tmp_path / "out", name="K", depends_on=("src",), mode=WriteMode.APPEND))
    outer = Pipeline("outer").add(PipelineUnit(inner, "K", name="N"))
    Runner(outer, checkpoint=FileCheckpoint(tmp_path / "cp")).run()
    assert Runner(outer, checkpoint=FileCheckpoint(tmp_path / "cp")).run().statuses["N"] is Status.REUSED
    import shutil; shutil.rmtree(tmp_path / "out")
    assert Runner(outer, checkpoint=FileCheckpoint(tmp_path / "cp")).run().statuses["N"] is Status.COMPLETE     # destination gone → not reused

