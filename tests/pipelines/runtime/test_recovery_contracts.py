# tests/pipelines/runtime/test_recovery_contracts.py — spec §8 verbatim, FileCheckpoint, fresh instance per run
import pytest
from mountainash.pipelines.core.pipeline import Pipeline
from mountainash.pipelines.core.values import *
from mountainash.pipelines.runtime.checkpoint import FileCheckpoint
from mountainash.pipelines.runtime.runner import Runner
from mountainash.pipelines.units.python import PythonUnit
from mountainash.pipelines.units.source import CallableSource
from mountainash.pipelines.errors import IncompatibleResume

A, B, C = "A", "B", "C"
def rows(*ps): return [{"p": p} for p in ps]

class LogSink(PythonUnit):
    """Reference-returning sink stand-in; liveness is destination-owned (here: always alive)."""
    def __init__(self, name, dep, fail_times=0):
        self.log, self._fail = [], fail_times
        super().__init__(self._fn, name=name, depends_on=(dep,))
    def _fn(self, rows_, ctx):
        if self._fail: self._fail -= 1; raise RuntimeError("sink down")
        self.log.append(rows_); return LocatorReference("mem://" + self.name, len(rows_))

def test_two_run_contract(tmp_path):
    calls = []
    def fetch(up, params, state):
        calls.append(state)
        if len(calls) == 1: return SourceResult(Value.of(rows(B), Identity.of("t"), Coverage.source({A, B}, {B}, {A})), None)
        want = state.outstanding | ({A, B, C} - state.succeeded)
        return SourceResult(Value.of(rows(*sorted(want)), Identity.of("t"), Coverage.source(want, want, set())), C)
    p = Pipeline("a").add(CallableSource(fetch, name="S")).add(LogSink("X", "S"))
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert FileCheckpoint(tmp_path).progress("S") == SourceState(None, frozenset({A}), frozenset({B}))
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert calls[1] == SourceState(None, frozenset({A}), frozenset({B})) and FileCheckpoint(tmp_path).progress("S") == SourceState(C, frozenset(), frozenset())

def test_interrupted_run_replays_and_commits_saved_cursor(tmp_path):
    calls = []
    def fetch(up, params, state):
        calls.append(state); return SourceResult(Value.of(rows(A), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    x = LogSink("X", "S", fail_times=1); p = Pipeline("b").add(CallableSource(fetch, name="S")).add(x)
    r = Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert r.statuses["X"] is Status.FAILED and FileCheckpoint(tmp_path).pending("S") is not None
    r = Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert len(calls) == 1 and x.log == [rows(A)] and FileCheckpoint(tmp_path).progress("S").cursor == A and FileCheckpoint(tmp_path).pending("S") is None

def test_two_pending_sources_first_compatible_second_incompatible_nothing_runs(tmp_path):   # Review Focus #2
    ran = []
    def fetch(up, params, state): return SourceResult(Value.of(rows(A), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    s1 = CallableSource(lambda u, p, st: (ran.append("S1"), fetch(u, p, st))[1], name="S1")
    s2 = CallableSource(lambda u, p, st: (ran.append("S2"), fetch(u, p, st))[1], name="S2")
    p = Pipeline("c").add(s1).add(s2).add(LogSink("X", "S1", fail_times=1)).add(LogSink("Y", "S2", fail_times=1))
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run(); ran.clear()
    s2.version = "2"                                                                  # only S2's configuration changed → S1 compatible, S2 incompatible
    with pytest.raises(IncompatibleResume):
        Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert ran == []

def test_partial_plus_two_sinks(tmp_path):
    calls = []
    def fetch(up, params, state):
        calls.append(state)
        if len(calls) == 1: return SourceResult(Value.of(rows(B), Identity.of("t"), Coverage.source({A, B}, {B}, {A})), None)
        return SourceResult(Value.of(rows(A), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    x, y = LogSink("X", "S"), LogSink("Y", "S", fail_times=1)
    p = Pipeline("d").add(CallableSource(fetch, name="S")).add(x).add(y)
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run(); Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert len(calls) == 1 and x.log == [rows(B)] and y.log == [rows(B)] and FileCheckpoint(tmp_path).progress("S").outstanding == frozenset({A})
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert x.log[-1] == rows(A) and y.log[-1] == rows(A) and FileCheckpoint(tmp_path).progress("S").cursor == A

def test_regenerate_replaces_attempt_and_reexecutes_descendants(tmp_path):
    import polars as pl
    calls, seen = [], []
    def fetch(up, params, state):
        calls.append(state); return SourceResult(Value.of(pl.DataFrame({"p": [A]}), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    def fetch_t(up, params, state):
        seen.append(up["S"].payload); return SourceResult(Value.of(rows(A), Identity.of("t2"), Coverage.source({A}, {A}, set())), A)
    p = Pipeline("e").add(CallableSource(fetch, name="S")).add(CallableSource(fetch_t, name="T", depends_on=("S",))).add(LogSink("X", "T", fail_times=1))
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run(); Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert len(calls) == 2 and len(seen) == 2 and seen[1] is not None            # S regenerated; T's pending retired → refetch against regenerated S
    assert FileCheckpoint(tmp_path).progress("S").cursor == A and FileCheckpoint(tmp_path).progress("T").cursor == A

def test_same_runner_two_runs_force_then_failure_keeps_attempt_pending(tmp_path):
    def fetch(up, params, state): return SourceResult(Value.of(rows(A), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    t = LogSink("T", "S", fail_times=0)
    p = Pipeline("f").add(CallableSource(fetch, name="S")).add(t)
    r = Runner(p, checkpoint=FileCheckpoint(tmp_path)); r.run()
    t._fail = 1; r.run(force=True)
    assert FileCheckpoint(tmp_path).pending("S") is not None                        # source-commit invariant (nested variant lives in 6c)

def test_force_discards_pending_even_if_replacement_fetch_fails(tmp_path):
    import polars as pl
    fail = [False]
    def fetch(up, params, state):
        if fail[0]: raise RuntimeError("new fetch failed")
        return SourceResult(Value.of(rows(A), Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    p = Pipeline("g").add(CallableSource(fetch, name="S")).add(LogSink("X", "S", fail_times=1))
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run(params={"revision": 1})
    assert FileCheckpoint(tmp_path).pending("S") is not None
    fail[0] = True
    r = Runner(p, checkpoint=FileCheckpoint(tmp_path)).run(params={"revision": 2}, force=True)
    assert r.statuses["S"] is Status.FAILED
    assert FileCheckpoint(tmp_path).pending("S") is None and FileCheckpoint(tmp_path).progress("S") == SourceState()
    fail[0] = False
    r = Runner(p, checkpoint=FileCheckpoint(tmp_path)).run(params={"revision": 2})          # no IncompatibleResume
    assert r.statuses["S"] is Status.COMPLETE

def test_regenerate_applies_empty_policy_fail(tmp_path):
    import polars as pl
    from mountainash.pipelines.core.policies import EmptyPolicy
    calls = []
    def fetch(up, params, state):
        calls.append(state)
        df = pl.DataFrame({"p": [1]}) if len(calls) == 1 else pl.DataFrame({"p": []}, schema={"p": pl.Int64})
        return SourceResult(Value.of(df, Identity.of("t"), Coverage.source({A}, {A}, set())), A)
    x = LogSink("X", "S", fail_times=1)
    p = Pipeline("h").add(CallableSource(fetch, name="S", empty=EmptyPolicy.FAIL)).add(x)
    Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert FileCheckpoint(tmp_path).pending("S").record.value is None               # not retained → REGENERATE next
    r = Runner(p, checkpoint=FileCheckpoint(tmp_path)).run()
    assert r.statuses["S"] is Status.FAILED and r.statuses["X"] is not Status.COMPLETE and x.log == []
    assert FileCheckpoint(tmp_path).progress("S") == SourceState()
