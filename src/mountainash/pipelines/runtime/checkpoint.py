from __future__ import annotations
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Protocol
from mountainash.pipelines.core.values import (
    Attempt,
    Coverage,
    Identity,
    LocatorReference,
    Record,
    SourceState,
    Status,
    Value,
    ValueKind,
)


class Checkpoint(Protocol):
    def lookup(self, unit: str, identity: Identity) -> Record | None: ...
    def record(self, unit: str, rec: Record) -> None: ...
    def progress(self, unit: str) -> SourceState: ...
    def set_progress(self, unit: str, state: SourceState) -> None: ...
    def pending(self, unit: str) -> Attempt | None: ...
    def pending_all(self) -> Iterable[tuple[tuple[str, ...], Attempt]]: ...
    def set_pending(self, unit: str, attempt: Attempt) -> None: ...
    def clear_pending(self, unit: str) -> None: ...
    def invalidate(self, units: set[str]) -> None: ...
    def scoped(self, name: str) -> "Checkpoint": ...
    def last_status(self, unit: str) -> Status | None: ...


class MemoryCheckpoint:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], Record] = {}
        self._progress: dict[str, SourceState] = {}
        self._pending: dict[str, Attempt] = {}
        self._status: dict[str, Status] = {}
        self._children: dict[str, MemoryCheckpoint] = {}
        self._lock = threading.RLock()

    def lookup(self, unit, identity):
        return self._records.get((unit, identity.digest))

    def last_status(self, unit):
        return self._status.get(unit)

    def record(self, unit, rec):
        with self._lock:
            self._records[(unit, rec.identity.digest)] = rec
            self._status[unit] = rec.status

    def progress(self, unit):
        return self._progress.get(unit, SourceState())

    def set_progress(self, unit, state):
        with self._lock:
            self._progress[unit] = state

    def pending(self, unit):
        return self._pending.get(unit)

    def pending_all(self):
        yield from (((u,), a) for u, a in list(self._pending.items()))
        for name, child in self._children.items():
            yield from (((name, *path), a) for path, a in child.pending_all())

    def set_pending(self, unit, attempt):
        with self._lock:
            self._pending[unit] = attempt
            self._status[unit] = attempt.record.status

    def clear_pending(self, unit):
        with self._lock:
            self._pending.pop(unit, None)

    def invalidate(self, units):
        with self._lock:
            self._records = {k: v for k, v in self._records.items() if k[0] not in units}
            for u in units:
                self._pending.pop(u, None)
                self._status.pop(u, None)

    def scoped(self, name):
        with self._lock:
            return self._children.setdefault(name, self._make_child(name))

    def _make_child(self, name):
        return MemoryCheckpoint()


# ---- JSON codec for FileCheckpoint ------------------------------------------------
def _enc_h(h: Any) -> Any:  # tagged, reversible encoding of the hashable vocabulary (F12)
    if isinstance(h, tuple):
        return {"__t__": [_enc_h(x) for x in h]}
    if isinstance(h, (str, int, float, bool)) or h is None:
        return h
    raise TypeError(f"partition/cursor value not encodable: {type(h).__name__}")


def _dec_h(d: Any) -> Any:
    return tuple(_dec_h(x) for x in d["__t__"]) if isinstance(d, dict) and "__t__" in d else d


def _enc_set(s) -> list:
    return [_enc_h(x) for x in s]  # unordered; equality is set equality


def _dec_set(items) -> frozenset:
    return frozenset(_dec_h(x) for x in items)


_UNRETAINED = {"__unretained__": True}


def _enc_value(v: Value | None) -> Any:
    if v is None:
        return None
    if v.kind is ValueKind.TABULAR:
        return _UNRETAINED
    if v.kind is ValueKind.REFERENCE:
        payload = {"locator": v.payload.locator, "record_count": v.payload.record_count}
    else:
        try:
            json.dumps(v.payload)
            payload = v.payload
        except TypeError:
            return _UNRETAINED
    return {"payload": payload, "identity": v.identity.digest, "kind": v.kind.value, "coverage": _enc_cov(v.coverage)}


def _dec_value(d: Any) -> Value | None:
    if d is None or d == _UNRETAINED:
        return None  # not retained → Record.value is None
    kind = ValueKind(d["kind"])
    p = d["payload"]
    if kind is ValueKind.REFERENCE and p is not None:
        p = LocatorReference(**p)
    return Value(p, Identity(d["identity"]), kind, None, _dec_cov(d["coverage"]))


def _enc_cov(c):
    return (
        None
        if c is None
        else {
            "attempted": _enc_set(c.attempted),
            "succeeded": _enc_set(c.succeeded),
            "failed": _enc_set(c.failed),
            "complete": c.complete,
        }
    )


def _dec_cov(d):
    return (
        None
        if d is None
        else Coverage(_dec_set(d["attempted"]), _dec_set(d["succeeded"]), _dec_set(d["failed"]), d["complete"])
    )


def _enc_state(s):
    return {"cursor": _enc_h(s.cursor), "outstanding": _enc_set(s.outstanding), "succeeded": _enc_set(s.succeeded)}


def _dec_state(d):
    return SourceState(_dec_h(d["cursor"]), _dec_set(d["outstanding"]), _dec_set(d["succeeded"]))


def _enc_rec(r):
    return {
        "identity": r.identity.digest,
        "status": r.status.value,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "coverage": _enc_cov(r.coverage),
        "value": _enc_value(r.value),
    }


def _dec_rec(d):
    return Record(
        Identity(d["identity"]),
        Status(d["status"]),
        datetime.fromisoformat(d["completed_at"]) if d["completed_at"] else None,
        _dec_cov(d["coverage"]),
        _dec_value(d["value"]),
    )


def _enc_att(a):
    return {
        "state_in": _enc_state(a.state_in),
        "identity": a.identity.digest,
        "record": _enc_rec(a.record),
        "next_cursor": _enc_h(a.next_cursor),
    }


def _dec_att(d):
    return Attempt(_dec_state(d["state_in"]), Identity(d["identity"]), _dec_rec(d["record"]), _dec_h(d["next_cursor"]))


def _fs(name: str) -> str:
    """Bounded, collision-resistant stem for any unit/scope name: sha256 hex prefix (32 chars). The original name is
    stored inside every JSON file (`"unit"`) and in `scopes/<stem>/name.json`, so loading never parses names from paths (F30/F36/P12)."""
    import hashlib

    return hashlib.sha256(name.encode("utf-8")).hexdigest()[:32]


class FileCheckpoint(MemoryCheckpoint):
    """One JSON file per record / attempt / progress under ``root``; scoped views are subdirectories."""

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._load()

    def _make_child(self, name):
        d = self.root / "scopes" / _fs(name)
        d.mkdir(parents=True, exist_ok=True)
        (d / "name.json").write_text(json.dumps(name))
        return FileCheckpoint(d)

    def _path(self, kind, unit, *rest):
        return self.root / kind / ("--".join((_fs(unit), *rest)) + ".json")  # ≤ 32+2+64 chars

    def _write(self, path, obj):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, sort_keys=True))

    def _load(self):
        for f in (self.root / "records").glob("*.json") if (self.root / "records").exists() else []:
            d = json.loads(f.read_text())
            self._records[(d["unit"], d["identity"])] = _dec_rec(d)
        for f in (self.root / "progress").glob("*.json") if (self.root / "progress").exists() else []:
            d = json.loads(f.read_text())
            self._progress[d["unit"]] = _dec_state(d["state"])
        for f in (self.root / "pending").glob("*.json") if (self.root / "pending").exists() else []:
            d = json.loads(f.read_text())
            self._pending[d["unit"]] = _dec_att(d["attempt"])
        st = self.root / "status.json"
        if st.exists():
            self._status = {k: Status(v) for k, v in json.loads(st.read_text()).items()}
        scopes = self.root / "scopes"
        if scopes.exists():
            for sub in scopes.iterdir():
                if sub.is_dir() and (sub / "name.json").exists():
                    self._children[json.loads((sub / "name.json").read_text())] = FileCheckpoint(sub)

    def _flush_status(self):
        with self._lock:  # snapshot + write under the lock (F31)
            self._write(self.root / "status.json", {k: v.value for k, v in self._status.items()})

    def record(self, unit, rec):
        with self._lock:
            super().record(unit, rec)
            self._write(self._path("records", unit, rec.identity.digest), {"unit": unit, **_enc_rec(rec)})
            self._flush_status()

    def set_progress(self, unit, state):
        with self._lock:
            super().set_progress(unit, state)
            self._write(self._path("progress", unit), {"unit": unit, "state": _enc_state(state)})

    def set_pending(self, unit, attempt):
        with self._lock:
            super().set_pending(unit, attempt)
            self._write(self._path("pending", unit), {"unit": unit, "attempt": _enc_att(attempt)})
            self._flush_status()

    def clear_pending(self, unit):
        with self._lock:
            super().clear_pending(unit)
            self._path("pending", unit).unlink(missing_ok=True)

    def invalidate(self, units):
        with self._lock:
            super().invalidate(units)
            for u in units:
                for f in (self.root / "records").glob(f"{_fs(u)}--*.json") if (self.root / "records").exists() else []:
                    f.unlink()
                self._path("pending", u).unlink(missing_ok=True)
            self._flush_status()
