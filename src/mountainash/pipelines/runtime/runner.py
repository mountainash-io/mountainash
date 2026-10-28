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

    # ---- phase 3 (completed in 6b/6c)
    def commit(self, plan: Plan, result: RunResult) -> None:                 # 6a version: flat graphs; 6c replaces it with the pending_all walk
        g = self.pipeline.graph
        ok = lambda names: all(result.statuses.get(d) in (Status.COMPLETE, Status.REUSED) for d in names)   # noqa: E731
        for path, _att in list(self.cp.pending_all()):
            if len(path) != 1 or path[0] not in result.statuses: continue     # nested (6c) or outside the selected subgraph
            n = path[0]
            u = g.nodes[n]; u.lifecycle.commit(u, ok(g.descendants(n)), self.cp)

    def run(self, *, params=None, target=None, resume=True, force=False) -> RunResult:
        plan = self.plan(params=params, target=target, resume=resume, force=force)
        result = self.execute(plan); self.commit(plan, result); return result

    # ---- collaborators
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
