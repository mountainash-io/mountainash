# src/mountainash/pipelines/runtime/lifecycle.py  (6a part; SourceLifecycle/NestedLifecycle appended in 6b/6c)
from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Mapping, Protocol
from mountainash.pipelines.core.values import Coverage, Identity, Record, SourceState, Status, Value, ValueKind


@dataclass(frozen=True)
class Identified:
    identity: Identity
    prepared: Any = None

@dataclass(frozen=True)
class Decision:
    tag: str
    record: Record | None = None
    attempt: Any = None
    state: SourceState | None = None

@dataclass(frozen=True)
class Outcome:
    identity: Identity
    status: Status
    value: Value | None


class Lifecycle(Protocol):
    @staticmethod
    def identify(unit, upstream: Mapping[str, Identity], params, cp, opts) -> Identified: ...
    @staticmethod
    def decide(unit, ident: Identified, cp, opts) -> Decision: ...
    @staticmethod
    def execute(unit, ident: Identified, decision: Decision, upstream: Mapping[str, Value], ctx, cp, runner, result) -> Outcome: ...
    @staticmethod
    def commit(unit, descendants_ok: bool, cp) -> None: ...


def _retained(rec: Record | None) -> bool:
    return rec is not None and rec.value is not None          # Record.value None == not retained (F13)


def propagate_coverage(unit, upstream: Mapping[str, Value]) -> Coverage | None:
    covs = [v.coverage for v in upstream.values()]
    if unit.partitions_preserved and len(covs) == 1:
        return covs[0]
    return None if all(c is None or c.complete for c in covs) else Coverage.partial_marker()


def normalise_output(unit, out: Any, identity: Identity, upstream: Mapping[str, Value]) -> Value:
    """Whatever a unit returned becomes a Value with THIS unit's identity and the propagated coverage (F11)."""
    cov = propagate_coverage(unit, upstream)
    if isinstance(out, Value):
        return replace(out, identity=identity, coverage=cov if cov is not None else out.coverage)
    return Value.of(out, identity, cov)


class UnitLifecycle:
    @staticmethod
    def identify(unit, upstream, params, cp, opts):
        return Identified(unit.identity(upstream, params, None))

    @staticmethod
    def decide(unit, ident, cp, opts):
        if opts["resume"] and not opts["force"]:
            rec = cp.lookup(unit.name, ident.identity)
            if rec and rec.status is Status.COMPLETE and _retained(rec) and (rec.value.kind is not ValueKind.REFERENCE or unit.reference_exists(rec.value.payload)):
                return Decision("REUSE", record=rec)
        return Decision("RUN")

    @staticmethod
    def execute(unit, ident, decision, upstream, ctx, cp, runner, result):
        if decision.tag == "REUSE":
            return Outcome(ident.identity, Status.REUSED, decision.record.value)
        out = runner.retrying(lambda: unit.run(upstream, ctx))
        v = normalise_output(unit, out, ident.identity, upstream)
        runner.apply_empty_policy(unit, v)
        cp.record(unit.name, Record(ident.identity, Status.COMPLETE, datetime.now(), v.coverage, v))
        return Outcome(ident.identity, Status.COMPLETE, v)

    @staticmethod
    def commit(unit, descendants_ok, cp): ...


def bind_lifecycles() -> None:
    from mountainash.pipelines.units.dag import DagUnit
    from mountainash.pipelines.units.python import PythonUnit
    from mountainash.pipelines.units.sinks.base import SinkUnit
    PythonUnit.lifecycle = DagUnit.lifecycle = SinkUnit.lifecycle = UnitLifecycle
    # SourceUnit / PipelineUnit bound in 6b / 6c
