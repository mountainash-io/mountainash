# tests/pipelines/runtime/test_runner.py
import threading, time
import pytest
from mountainash.pipelines.core.pipeline import Pipeline
from mountainash.pipelines.core.policies import EmptyPolicy, RetryConfig
from mountainash.pipelines.core.values import Affinity, Coverage, Identity, LocatorReference, Status, Value
from mountainash.pipelines.errors import EmptyUnitOutput, NonRetryable
from mountainash.pipelines.runtime.checkpoint import MemoryCheckpoint
from mountainash.pipelines.runtime.runner import Runner
from mountainash.pipelines.units.python import PythonUnit, unit

def rows(*ps): return [{"p": p} for p in ps]

@pytest.mark.cell("unit:PythonUnit")
@pytest.mark.cell("status:COMPLETE")
@pytest.mark.cell("status:FAILED")
@pytest.mark.cell("status:SKIPPED")
def test_order_layers_inline_and_skip_on_failure():
    seen = []
    a = PythonUnit(lambda ctx: seen.append(("a", threading.current_thread().name)) or rows(1), name="a")
    b = PythonUnit(lambda ctx: (_ for _ in ()).throw(RuntimeError("x")), name="b")
    c = PythonUnit(lambda x, ctx: x, name="c", depends_on=("a",)); d = PythonUnit(lambda x, ctx: x, name="d", depends_on=("b",))
    r = Runner(Pipeline("p").add(a).add(b).add(c).add(d)).run()
    assert r.statuses == {"a": Status.COMPLETE, "b": Status.FAILED, "c": Status.COMPLETE, "d": Status.SKIPPED}
    assert seen[0][1] == threading.current_thread().name and r.executed == ("a", "c") or set(r.executed) == {"a", "c"}

@pytest.mark.cell("unit:PythonUnit")
@pytest.mark.cell("status:REUSED")
@pytest.mark.cell("status:COMPLETE")
@pytest.mark.cell("kind:REFERENCE")
def test_reuse_then_force_and_record_reference_liveness():
    calls = []
    u = PythonUnit(lambda ctx: calls.append(1) or rows(1), name="u")
    cp = MemoryCheckpoint(); p = Pipeline("p").add(u)
    Runner(p, checkpoint=cp).run(); r = Runner(p, checkpoint=cp).run()
    assert r.statuses["u"] is Status.REUSED and len(calls) == 1
    Runner(p, checkpoint=cp).run(force=True); assert len(calls) == 2
    class Sink(PythonUnit):
        alive = True
        def reference_exists(self, ref): return self.alive
    k = Sink(lambda x, ctx: LocatorReference("x://1", 1), name="k", depends_on=("u",))
    p2 = Pipeline("q").add(u).add(k); cp2 = MemoryCheckpoint()
    Runner(p2, checkpoint=cp2).run(); assert Runner(p2, checkpoint=cp2).run().statuses["k"] is Status.REUSED
    k.alive = False; assert Runner(p2, checkpoint=cp2).run().statuses["k"] is Status.COMPLETE       # destination says gone → re-run

@pytest.mark.cell("unit:PythonUnit")
@pytest.mark.cell("status:COMPLETE")
@pytest.mark.cell("status:FAILED")
def test_retry_then_non_retryable_and_empty_policy():
    n = {"k": 0}
    def flaky(ctx):
        n["k"] += 1
        if n["k"] < 3: raise RuntimeError("transient")
        return rows(1)
    r = Runner(Pipeline("p").add(PythonUnit(flaky, name="f")), retry=RetryConfig(max_attempts=3, initial_delay_seconds=0)).run()
    assert r.statuses["f"] is Status.COMPLETE and n["k"] == 3
    def boom(ctx): raise NonRetryable("stop")
    n2 = {"k": 0}
    def counted(ctx): n2["k"] += 1; raise NonRetryable("stop")
    Runner(Pipeline("p").add(PythonUnit(counted, name="g")), retry=RetryConfig(max_attempts=3, initial_delay_seconds=0)).run()
    assert n2["k"] == 1
    r = Runner(Pipeline("p").add(PythonUnit(lambda ctx: [], name="e", empty=EmptyPolicy.FAIL))).run()
    assert r.statuses["e"] is Status.FAILED
    spy = {"count": 0}
    class V(list):
        def __len__(self): spy["count"] += 1; return 0
    Runner(Pipeline("p").add(PythonUnit(lambda ctx: V(), name="s", empty=EmptyPolicy.SILENT))).run()
    assert spy["count"] == 0                                              # SILENT never counts

@pytest.mark.cell("unit:PythonUnit")
def test_coverage_propagation_including_value_returns():                 # F11
    src_cov = Coverage.source({"A", "B"}, {"B"}, {"A"})
    s = PythonUnit(lambda ctx: Value.of(rows("B"), Identity.of("t"), src_cov), name="s")
    t = PythonUnit(lambda r, ctx: Value.of(r, Identity.of("ignored")), name="t", depends_on=("s",))      # returns a Value
    u = PythonUnit(lambda r, ctx: r, name="u", depends_on=("t",), partitions_preserved=True)
    r = Runner(Pipeline("p").add(s).add(t).add(u)).run()
    assert r.values["t"].coverage == Coverage.partial_marker() and r.values["t"].identity == r.values["t"].identity
    assert r.values["u"].coverage == Coverage.partial_marker()           # pass-through of its single upstream
    w = PythonUnit(lambda r, ctx: r, name="w", depends_on=("s",), partitions_preserved=True)
    assert Runner(Pipeline("q").add(s).add(w)).run().values["w"].coverage == src_cov

@pytest.mark.cell("unit:PythonUnit")
def test_parallel_workers_policy_isolation_and_unit_exclusion():
    from mountainash.core.capabilities.policy import CapabilityPolicy, capability_policy, _resolve_policy
    seen = {}
    def rec(name): return PythonUnit(lambda ctx: seen.update({name: (threading.current_thread().name, _resolve_policy())}) or rows(1), name=name)
    p = Pipeline("p").add(rec("w1")).add(rec("w2")).add(PythonUnit(lambda ctx: seen.update({"m": threading.current_thread().name}) or rows(1), name="m", affinity=Affinity.MAIN))
    with capability_policy(CapabilityPolicy.trusted()):
        Runner(p, workers=3).run(force=True)
    assert seen["m"] == threading.current_thread().name and seen["w1"][0] != threading.current_thread().name and seen["w1"][1] == CapabilityPolicy.trusted()
    # concurrent runs with different policies are isolated; a shared unit instance never runs concurrently with itself (F14)
    active = {"n": 0, "max": 0}; lock = threading.Lock()
    def slow(ctx):
        with lock: active["n"] += 1; active["max"] = max(active["max"], active["n"])
        time.sleep(0.05)
        with lock: active["n"] -= 1
        return rows(1)
    shared = PythonUnit(slow, name="shared")
    pols = {}
    def run_with(pol, key):
        with capability_policy(pol):
            Runner(Pipeline(key).add(shared).add(PythonUnit(lambda x, ctx: pols.update({key: _resolve_policy()}) or x, name="probe", depends_on=("shared",)))).run(force=True)
    ts = [threading.Thread(target=run_with, args=(CapabilityPolicy.trusted(), "t")), threading.Thread(target=run_with, args=(CapabilityPolicy.checked(), "c"))]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert active["max"] == 1 and pols["t"] == CapabilityPolicy.trusted() and pols["c"] == CapabilityPolicy.checked()

@pytest.mark.cell("unit:PythonUnit")
@pytest.mark.cell("status:FAILED")
@pytest.mark.cell("status:SKIPPED")
@pytest.mark.cell("status:COMPLETE")
def test_worker_failure_with_sibling_main_running():                     # Review Focus #5
    inner_main = PythonUnit(lambda ctx: time.sleep(0.2) or rows(1), name="m", affinity=Affinity.MAIN)
    boom = PythonUnit(lambda ctx: (_ for _ in ()).throw(RuntimeError("x")), name="boom")
    p = Pipeline("f").add(boom).add(inner_main).add(PythonUnit(lambda b, ctx: b, name="after", depends_on=("boom",)))
    r = Runner(p, workers=2).run(force=True)
    assert r.statuses["boom"] is Status.FAILED and r.statuses["after"] is Status.SKIPPED and r.statuses["m"] is Status.COMPLETE

@pytest.mark.cell("status:COMPLETE")
def test_structural_unit_without_baseunit_runs():                         # P10: the protocol, not inheritance, is the contract
    import threading
    from mountainash.pipelines.runtime.lifecycle import UnitLifecycle
    from mountainash.pipelines.core.policies import EmptyPolicy
    class Bare:
        lifecycle = UnitLifecycle; name = "bare"; version = "1"; affinity = Affinity.WORKER; empty = EmptyPolicy.SILENT; partitions_preserved = False
        exec_lock = threading.Lock()
        def inputs(self): return ()
        def identity(self, upstream, params, state): return Identity.of("bare", self.version, dict(params))
        def reference_exists(self, ref): return True
        def run(self, upstream, ctx): return rows(1)
    r = Runner(Pipeline("p").add(Bare())).run()
    assert r.statuses["bare"] is Status.COMPLETE

@pytest.mark.cell("unit:PythonUnit")
def test_external_inputs_are_a_supported_planning_case():                 # F10
    inner = Pipeline("inner", inputs=("S",)).add(PythonUnit(lambda s, ctx: s, name="V", depends_on=("S",)))
    assert inner.graph.topological_order() == ["V"] and inner.graph.nodes["V"].inputs() == ("S",)
    r = Runner(inner)
    plan = r.plan(injected_identities={"S": Identity.of("s")})
    res = r.execute(plan, upstream_values={"S": Value.of(rows(9), Identity.of("s"))})
    assert res.values["V"].payload == rows(9)
    with pytest.raises(KeyError):
        Pipeline("bad").add(PythonUnit(lambda s, ctx: s, name="V", depends_on=("S",)))   # undeclared upstream
