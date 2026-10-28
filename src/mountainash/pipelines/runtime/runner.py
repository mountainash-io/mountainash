# src/mountainash/pipelines/runtime/runner.py  (6a; invalidate_descendants / register_nested completed in 6b/6c)
from __future__ import annotations
import logging, threading, time, uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping
from mountainash.pipelines.core.policies import EmptyPolicy, RetryConfig
from mountainash.pipelines.core.values import Affinity, Identity, RunContext, Status, Value
from mountainash.pipelines.errors import EmptyUnitOutput, NonRetryable
from mountainash.pipelines.runtime.checkpoint import Checkpoint, MemoryCheckpoint
from mountainash.pipelines.runtime.lifecycle import Identified, bind_lifecycles

bind_lifecycles()
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunScope:
    checkpoint: Checkpoint
    options: Mapping[str, Any]


@dataclass
class Plan:
    order: list[str]
    layers: list[list[str]]
    identified: dict[str, Identified]
    options: dict[str, Any]
    def identity_of(self, name: str) -> Identity: return self.identified[name].identity


@dataclass
class RunResult:
    values: dict[str, Value] = field(default_factory=dict)
    statuses: dict[str, Status] = field(default_factory=dict)
    executed: tuple[str, ...] = ()
    run_id: str = ""
    nested: dict[str, tuple[Any, Plan, "RunResult"]] = field(default_factory=dict)      # per run (F8)


class Runner:
    def __init__(self, pipeline, *, checkpoint: Checkpoint | None = None, workers: int = 1, retry: RetryConfig | None = None) -> None:
        self.pipeline = pipeline; self.cp = checkpoint or MemoryCheckpoint(); self.workers = workers; self.retry = retry
        self.enclosing: tuple[Runner, str] | None = None        # (outer runner, PipelineUnit name); set by NestedLifecycle while the inner run executes

    # ---- phase 1
    def plan(self, *, params=None, target=None, resume=True, force=False, injected_identities: Mapping[str, Identity] | None = None) -> Plan:
        opts = {"resume": resume, "force": force, "workers": self.workers, "retry": self.retry, "params": dict(params or {}), "config": {}}
        order = self.pipeline.graph.topological_order(target)
        identified: dict[str, Identified] = {}
        injected = dict(injected_identities or {})
        for n in order:
            u = self.pipeline.graph.nodes[n]
            up = {d: (identified[d].identity if d in identified else injected[d]) for d in u.inputs()}
            identified[n] = u.lifecycle.identify(u, up, opts["params"], self.cp, opts)
        return Plan(order, self.pipeline.graph.parallel_layers(order), identified, opts)

    # ---- phase 2
    def execute(self, plan: Plan, *, upstream_values: Mapping[str, Value] | None = None) -> RunResult:
        from mountainash.core.capabilities.policy import _resolve_policy, capability_policy
        frozen = _resolve_policy()
        result = RunResult(run_id=uuid.uuid4().hex)
        values: dict[str, Value] = dict(upstream_values or {})
        lock = threading.Lock()

        def run_one(n: str) -> None:
            u = self.pipeline.graph.nodes[n]
            if any(result.statuses.get(d) in (Status.FAILED, Status.SKIPPED) for d in u.inputs() if d in plan.identified):
                with lock: result.statuses[n] = Status.SKIPPED
                return
            ctx = RunContext(plan.options["params"], None, plan.options["config"], self.pipeline.name, n, result.run_id)
            with capability_policy(frozen), u.exec_lock:                       # policy re-entry (B3); per-instance exclusion (F14)
                try:
                    dec = u.lifecycle.decide(u, plan.identified[n], self.cp, plan.options)
                    out = u.lifecycle.execute(u, plan.identified[n], dec, {d: values[d] for d in u.inputs()}, ctx, self.cp, self, result)
                    with lock:
                        result.statuses[n] = out.status; values[n] = out.value
                        if out.status is not Status.REUSED: result.executed += (n,)
                except Exception:                                               # noqa: BLE001 — recorded as FAILED
                    log.exception("unit %s failed", n)
                    with lock: result.statuses[n] = Status.FAILED

        for layer in plan.layers:
            mains = [n for n in layer if self.pipeline.graph.nodes[n].affinity is Affinity.MAIN]
            others = [n for n in layer if n not in mains]
            if self.workers == 1:
                for n in layer: run_one(n)
            else:
                with ThreadPoolExecutor(self.workers) as ex:
                    futs = [ex.submit(run_one, n) for n in others]
                    for n in mains: run_one(n)
                    for f in futs: f.result()
        result.values = {k: v for k, v in values.items() if k in plan.identified}
        return result

    # ---- phase 3
    def register_nested(self, result: RunResult, name: str, inner: "Runner", plan: Plan, inner_result: RunResult) -> None:
        result.nested[name] = (inner, plan, inner_result)

    def commit(self, plan: Plan, result: RunResult) -> None:
        """Spec §7: enumerate every pending attempt in the checkpoint and its scoped views; commit those whose source is in
        this run's selected subgraph (resolving nested paths through the run's nested results / prepared plans)."""
        for path, _attempt in list(self.cp.pending_all()):                  # path is a tuple of raw names (F38/P13)
            frame = self._resolve_pending(list(path), self.cp, self.pipeline, result, plan, outer_ok=True)
            if frame is None: continue                                   # outside the selected subgraph → untouched
            unit, scoped_cp, descendants_ok = frame
            unit.lifecycle.commit(unit, descendants_ok, scoped_cp)

    def _resolve_pending(self, path, cp, pipeline, result, plan, outer_ok):
        """Walk a pending-attempt path (``N/M/S``) through nested pipelines; return (unit, its checkpoint, descendants_ok) or None."""
        from mountainash.pipelines.units.nested import PipelineUnit
        g = pipeline.graph; head, rest = path[0], path[1:]
        if head not in result.statuses: return None
        ok = lambda names: all(result.statuses.get(d) in (Status.COMPLETE, Status.REUSED) for d in names)   # noqa: E731
        u = g.nodes[head]
        if not rest:
            return (u, cp, outer_ok and ok(g.descendants(head)))
        if not isinstance(u, PipelineUnit): return None
        outer_desc_ok = outer_ok and ok(g.descendants(head))
        scoped = cp.scoped(head)
        if head in result.nested:                                        # executed this run: real inner statuses
            inner, inner_plan, inner_result = result.nested[head]
            return inner._resolve_pending(rest, scoped, u.pipeline, inner_result, inner_plan, outer_desc_ok)
        if result.statuses[head] is Status.REUSED:                       # reused this run: last recorded inner statuses, selected subgraph only (spec §7 / F7)
            inner, inner_plan = plan.identified[head].prepared
            synth = RunResult(statuses={k: (Status.REUSED if st is Status.COMPLETE else st) for k in inner_plan.order if (st := scoped.last_status(k)) is not None})
            return inner._resolve_pending(rest, scoped, u.pipeline, synth, inner_plan, outer_desc_ok)
        return None

    def run(self, *, params=None, target=None, resume=True, force=False) -> RunResult:
        plan = self.plan(params=params, target=target, resume=resume, force=force)
        result = self.execute(plan); self.commit(plan, result); return result

    # ---- collaborators
    def invalidate_descendants(self, name: str) -> None:
        """Retire records and pending attempts of exactly the transitive descendants of ``name`` (F9/F10): in this graph,
        and inside every nested PipelineUnit that consumes ``name`` or one of its descendants as an external input. A regeneration
        inside a nested pipeline also changes that PipelineUnit's output, so the enclosing runners retire their descendants too."""
        self._invalidate_in(self.cp, self.pipeline, {name})
        if self.enclosing is not None:
            outer, unit_name = self.enclosing
            outer.invalidate_descendants(unit_name)

    def _invalidate_in(self, cp, pipeline, changed: set[str]) -> None:
        from mountainash.pipelines.units.nested import PipelineUnit
        g = pipeline.graph
        desc: set[str] = set()
        for c in changed:
            desc |= g.descendants(c) if c in g.nodes else pipeline.consumers_of(c) | {d for k in pipeline.consumers_of(c) for d in g.descendants(k)}
        cp.invalidate(desc)
        for d in desc:
            u = g.nodes[d]
            if isinstance(u, PipelineUnit):
                outer_changed = {x for x in u.inputs() if x in desc or x in changed}
                self._invalidate_in(cp.scoped(d), u.pipeline, outer_changed if outer_changed else set(u.inputs()))

    def retrying(self, fn: Callable[[], Any]) -> Any:
        attempts = self.retry.max_attempts if self.retry else 1
        delay = self.retry.initial_delay_seconds if self.retry else 0.0
        for i in range(attempts):
            try: return fn()
            except NonRetryable: raise
            except Exception:
                if i == attempts - 1: raise
                time.sleep(delay); delay *= (self.retry.backoff_rate if self.retry else 1.0)

    def apply_empty_policy(self, unit, v: Value) -> None:
        if unit.empty is EmptyPolicy.SILENT: return
        if v.is_empty():
            if unit.empty is EmptyPolicy.FAIL: raise EmptyUnitOutput(f"{unit.name} returned empty data")
            log.warning("unit %s returned empty data", unit.name)
