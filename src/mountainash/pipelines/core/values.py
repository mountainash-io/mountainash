from __future__ import annotations
import hashlib
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Hashable, Mapping, Protocol, runtime_checkable
from mountainash.pipelines.errors import UnhashableIdentityInput


class ValueKind(Enum): TABULAR = "tabular"; RECORDS = "records"; REFERENCE = "reference"; OPAQUE = "opaque"
class Status(Enum): COMPLETE = "complete"; PARTIAL = "partial"; FAILED = "failed"; SKIPPED = "skipped"; REUSED = "reused"
class Affinity(Enum): WORKER = "worker"; MAIN = "main"

Partition = Hashable
Cursor = Hashable


@dataclass(frozen=True)
class Identity:
    digest: str

    @classmethod
    def of(cls, *parts: Any) -> "Identity":
        from mountainash.typespec._fingerprint import declaration_fingerprint, freeze_declaration
        try:
            frozen = freeze_declaration(_canonical(parts))
            return cls(declaration_fingerprint(frozen)[:32])
        except (TypeError, ValueError) as e:
            raise UnhashableIdentityInput(str(e)) from e


def _canonical(o: Any) -> Any:
    """Reduce identity operands to the fingerprint vocabulary WITHOUT collapsing distinctions (plan review F5):
    mappings stay mappings, sequences stay tuples, sets become a tagged tuple ordered by member fingerprint
    (no value ordering — heterogeneous members allowed, F12), dates/decimals/bytes pass through to the shared encoder."""
    from mountainash.typespec._fingerprint import declaration_fingerprint, freeze_declaration
    if isinstance(o, Identity): return {"__id__": o.digest}
    if isinstance(o, Enum): return {"__enum__": o.value}
    if isinstance(o, (frozenset, set)):
        members = [_canonical(x) for x in o]
        return {"__set__": tuple(m for _, m in sorted((declaration_fingerprint(freeze_declaration(m)), m) for m in members))}
    if isinstance(o, (list, tuple)): return tuple(_canonical(x) for x in o)
    if isinstance(o, Mapping):
        if not all(isinstance(k, str) for k in o): raise TypeError("identity mapping keys must be str")   # no repr() collisions (F5)
        return {"__map__": {k: _canonical(v) for k, v in o.items()}}
    if hasattr(o, "__dataclass_fields__"): return {"__dc__": type(o).__name__, **{f: _canonical(getattr(o, f)) for f in o.__dataclass_fields__}}
    return o          # str/int/float/bool/None/date/time/timedelta/Decimal/bytes: the shared encoder validates


@dataclass(frozen=True)
class Coverage:
    attempted: frozenset = frozenset(); succeeded: frozenset = frozenset(); failed: frozenset = frozenset(); complete: bool = True

    @classmethod
    def source(cls, attempted, succeeded, failed) -> "Coverage":
        a, s, f = frozenset(attempted), frozenset(succeeded), frozenset(failed)
        return cls(a, s, f, complete=not f)

    @classmethod
    def partial_marker(cls) -> "Coverage":
        return cls(complete=False)


@dataclass(frozen=True)
class SourceState:
    cursor: Cursor | None = None
    outstanding: frozenset = frozenset()
    succeeded: frozenset = frozenset()

    def advance(self, coverage: Coverage, next_cursor: Cursor | None) -> "SourceState":
        residual = (self.outstanding | coverage.failed) - coverage.succeeded
        if not residual:
            return SourceState(next_cursor, frozenset(), frozenset())
        return SourceState(self.cursor, residual, self.succeeded | coverage.succeeded)


@runtime_checkable
class Reference(Protocol):
    locator: str
    record_count: int | None


@dataclass(frozen=True)
class LocatorReference:
    """Plain data. Liveness is answered by the producing unit (``BaseUnit.reference_exists``), never here."""
    locator: str
    record_count: int | None = None


def _is_frame_carrier(payload: Any) -> bool:
    if payload is None or isinstance(payload, (str, bytes, int, float, bool, Enum, list, dict, tuple, set)):
        return False
    from mountainash.core.lazy_imports import is_available
    if is_available("pyarrow"):
        import pyarrow as pa
        if isinstance(payload, pa.Table):
            return True
    from mountainash.core.backend_detection import native_identity
    try:
        native_identity(payload); return True
    except Exception:
        return False


def _location_of(payload: Any) -> Any:
    from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
    return LocationResolver(IdentityTokens())._read(payload)


@dataclass(frozen=True)
class Value:
    payload: Any
    identity: Identity
    kind: ValueKind
    location: Any = None
    coverage: Coverage | None = None

    @classmethod
    def of(cls, payload: Any, identity: Identity, coverage: Coverage | None = None) -> "Value":
        if isinstance(payload, Reference):
            return cls(payload, identity, ValueKind.REFERENCE, None, coverage)
        if isinstance(payload, list) and all(isinstance(r, Mapping) for r in payload):
            return cls(payload, identity, ValueKind.RECORDS, None, coverage)
        if isinstance(payload, dict) and all(isinstance(v, list) for v in payload.values()):
            return cls(payload, identity, ValueKind.RECORDS, None, coverage)
        if _is_frame_carrier(payload):
            return cls(payload, identity, ValueKind.TABULAR, _location_of(payload), coverage)
        return cls(payload, identity, ValueKind.OPAQUE, None, coverage)

    def record_count(self) -> int | None:
        if self.kind is ValueKind.RECORDS:
            return len(self.payload) if isinstance(self.payload, list) else len(next(iter(self.payload.values()), []))
        if self.kind is ValueKind.REFERENCE:
            return self.payload.record_count
        if self.kind is ValueKind.TABULAR:
            from mountainash.relations.core.relation_api.relation import relation
            return relation(self.payload).count_rows()       # family-native count; executes a lazy input only here
        return None

    def is_empty(self) -> bool | None:
        n = self.record_count()
        return None if n is None else n == 0


@dataclass(frozen=True)
class SourceResult:
    value: Value
    next_cursor: Cursor | None


@dataclass(frozen=True)
class Record:
    identity: Identity
    status: Status
    completed_at: datetime | None
    coverage: Coverage | None
    value: Value | None


@dataclass(frozen=True)
class Attempt:
    state_in: SourceState
    identity: Identity
    record: Record
    next_cursor: Cursor | None

    def replace(self, result: SourceResult) -> "Attempt":
        cov = result.value.coverage
        st = Status.COMPLETE if (cov is None or cov.complete) else Status.PARTIAL
        return Attempt(self.state_in, self.identity, Record(self.identity, st, datetime.now(), cov, result.value), result.next_cursor)

    def commit(self) -> SourceState:
        return self.state_in.advance(self.record.coverage or Coverage(), self.next_cursor)


@dataclass(frozen=True)
class RunContext:
    params: Mapping[str, Any]
    state: SourceState | None
    config: Mapping[str, Any]
    pipeline_name: str
    unit_name: str
    run_id: str
