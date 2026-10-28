# tests/pipelines/runtime/test_checkpoint.py
import polars as pl, pytest
from datetime import datetime
from mountainash.pipelines.core.values import (Attempt, Coverage, Identity, LocatorReference, Record, SourceState, Status, Value, ValueKind)
from mountainash.pipelines.runtime.checkpoint import FileCheckpoint, MemoryCheckpoint

def _rec(payload, st=Status.COMPLETE):
    v = Value.of(payload, Identity.of("i")); return Record(v.identity, st, datetime.now(), None, v)

@pytest.fixture(params=["memory", "file"])
def cp(request, tmp_path):
    return MemoryCheckpoint() if request.param == "memory" else FileCheckpoint(tmp_path)

@pytest.mark.cell("checkpoint:MemoryCheckpoint")
@pytest.mark.cell("checkpoint:FileCheckpoint")
def test_record_lookup_progress_pending_roundtrip(cp, tmp_path):
    cp.record("u", _rec([{"a": 1}]))
    assert cp.lookup("u", Identity.of("i")).value.payload == [{"a": 1}]
    st = SourceState("C", frozenset({"A"}), frozenset({"B"}))
    cp.set_progress("s", st); assert cp.progress("s") == st
    att = Attempt(SourceState(), Identity.of("i"), _rec([{"p": "B"}], Status.PARTIAL), "B")
    cp.set_pending("s", att); assert cp.pending("s") == att
    if isinstance(cp, FileCheckpoint):                      # survives a fresh instance (process restart)
        again = FileCheckpoint(tmp_path)
        assert again.progress("s") == st and again.pending("s") == att and again.lookup("u", Identity.of("i")).value.payload == [{"a": 1}]
    cp.clear_pending("s"); assert cp.pending("s") is None

@pytest.mark.cell("checkpoint:MemoryCheckpoint")
@pytest.mark.cell("checkpoint:FileCheckpoint")
@pytest.mark.cell("status:COMPLETE")
def test_file_checkpoint_never_serialises_tabular(tmp_path):
    cp = FileCheckpoint(tmp_path)
    cp.record("u", _rec(pl.DataFrame({"a": [1]})))
    again = FileCheckpoint(tmp_path).lookup("u", Identity.of("i"))
    assert again.value is None and again.status is Status.COMPLETE                 # TABULAR is not retained: Record.value is None
    assert MemoryCheckpoint().record("u", _rec(pl.DataFrame({"a": [1]}))) is None   # memory retains by reference (no error)

@pytest.mark.cell("checkpoint:MemoryCheckpoint")
@pytest.mark.cell("checkpoint:FileCheckpoint")
@pytest.mark.cell("kind:REFERENCE")
def test_reference_roundtrip_and_scoped_pending_all(cp, tmp_path):
    cp.record("k", _rec(LocatorReference("mem://t", 3)))
    assert cp.lookup("k", Identity.of("i")).value.payload == LocatorReference("mem://t", 3)
    inner = cp.scoped("N")
    att = Attempt(SourceState(), Identity.of("i"), _rec([{"p": 1}]), "A")
    inner.set_pending("S", att); cp.set_pending("T", att)
    assert sorted(p for p, _ in cp.pending_all()) == [("N", "S"), ("T",)]
    if isinstance(cp, FileCheckpoint):
        assert sorted(p for p, _ in FileCheckpoint(tmp_path).pending_all()) == [("N", "S"), ("T",)]

@pytest.mark.cell("checkpoint:MemoryCheckpoint")
@pytest.mark.cell("checkpoint:FileCheckpoint")
@pytest.mark.cell("status:PARTIAL")
def test_last_status_and_tagged_partitions_and_names(cp, tmp_path):
    att = Attempt(SourceState(("k", 1), frozenset({1, "A", ("x", 2)}), frozenset()), Identity.of("i"), _rec([{"p": 1}], Status.PARTIAL), ("c", 9))
    cp.set_pending("tenant/fetch__daily", att)
    assert cp.last_status("tenant/fetch__daily") is Status.PARTIAL and cp.pending("tenant/fetch__daily") == att
    cp.record("u", _rec(None))                                       # legitimate OPAQUE None is retained
    assert cp.lookup("u", Identity.of("i")).value is not None and cp.lookup("u", Identity.of("i")).value.payload is None
    if isinstance(cp, FileCheckpoint):
        again = FileCheckpoint(tmp_path)
        assert again.pending("tenant/fetch__daily") == att and again.last_status("tenant/fetch__daily") is Status.PARTIAL


@pytest.mark.cell("checkpoint:FileCheckpoint")
def test_delimiter_bearing_and_dotted_names_roundtrip_and_invalidate_selectively(tmp_path):     # F30
    cp = FileCheckpoint(tmp_path)
    cp.record("fetch--daily", _rec([{"x": 1}])); cp.record("fetch", _rec([{"x": 2}]))
    cp.scoped("..").record("inner", _rec([{"x": 3}]))
    again = FileCheckpoint(tmp_path)
    assert again.lookup("fetch--daily", Identity.of("i")).value.payload == [{"x": 1}] and again.lookup("fetch", Identity.of("i")).value.payload == [{"x": 2}]
    assert again.scoped("..").lookup("inner", Identity.of("i")) is not None and (tmp_path / "scopes").exists() and not (tmp_path.parent / "records").exists()
    again.invalidate({"fetch"})
    assert FileCheckpoint(tmp_path).lookup("fetch--daily", Identity.of("i")) is not None

@pytest.mark.cell("checkpoint:FileCheckpoint")
def test_long_names_persist_within_filesystem_limits(tmp_path):                     # F36/P12
    cp = FileCheckpoint(tmp_path); long = "u" * 300
    cp.record(long, _rec([{"x": 1}])); cp.scoped(long).set_progress(long, SourceState("c"))
    again = FileCheckpoint(tmp_path)
    assert again.lookup(long, Identity.of("i")) is not None and again.scoped(long).progress(long).cursor == "c"

@pytest.mark.cell("checkpoint:FileCheckpoint")
@pytest.mark.cell("status:COMPLETE")
def test_parallel_record_writes_are_serialised(tmp_path):
    import threading
    cp = FileCheckpoint(tmp_path)
    ts = [threading.Thread(target=lambda i=i: cp.record(f"u{i}", _rec([{"i": i}]))) for i in range(8)]
    [t.start() for t in ts]; [t.join() for t in ts]
    again = FileCheckpoint(tmp_path)
    assert all(again.lookup(f"u{i}", Identity.of("i")) is not None and again.last_status(f"u{i}") is Status.COMPLETE for i in range(8))


@pytest.mark.cell("checkpoint:MemoryCheckpoint")
@pytest.mark.cell("checkpoint:FileCheckpoint")
def test_invalidate_exact_units_only(cp):
    cp.record("a", _rec([{"x": 1}])); cp.record("b", _rec([{"x": 2}]))
    att = Attempt(SourceState(), Identity.of("i"), _rec([{"p": 1}]), None)
    cp.set_pending("a", att); cp.set_pending("b", att)
    cp.invalidate({"a"})
    assert cp.lookup("a", Identity.of("i")) is None and cp.pending("a") is None
    assert cp.lookup("b", Identity.of("i")) is not None and cp.pending("b") is not None


@pytest.mark.cell("checkpoint:FileCheckpoint")
@pytest.mark.parametrize("payload", [(1, 2), {1: "a"}, [(1, 2)], {"k": {2: "b"}}, {"k": (1,)}])
def test_file_checkpoint_never_returns_a_silently_altered_payload(tmp_path, payload):
    cp = FileCheckpoint(tmp_path)
    cp.record("u", _rec(payload))
    again = FileCheckpoint(tmp_path).lookup("u", Identity.of("i"))
    assert again.value is None or (again.value.payload == payload and type(again.value.payload) is type(payload))


@pytest.mark.cell("checkpoint:FileCheckpoint")
def test_file_checkpoint_retains_faithful_json_payload(tmp_path):
    payload = {"a": [1, 2.5, "x", None, True], "b": {"c": []}}
    FileCheckpoint(tmp_path).record("u", _rec(payload))
    assert FileCheckpoint(tmp_path).lookup("u", Identity.of("i")).value.payload == payload
