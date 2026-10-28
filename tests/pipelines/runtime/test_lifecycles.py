# tests/pipelines/runtime/test_lifecycles.py
import pytest
from mountainash.pipelines.core.values import *
from mountainash.pipelines.runtime.checkpoint import MemoryCheckpoint

OPTS = {"resume": True, "force": False}

from mountainash.pipelines.runtime.lifecycle import SourceLifecycle
from mountainash.pipelines.units.source import CallableSource
from mountainash.pipelines.errors import IncompatibleResume

def test_source_lifecycle_identify_raises_on_incompatible_pending():
    s = CallableSource(lambda u, p, st: None, name="s"); cp = MemoryCheckpoint()
    att = Attempt(SourceState(), s.identity({}, {"t": 1}, SourceState()), Record(Identity.of("x"), Status.COMPLETE, None, None, None), "A")
    cp.set_pending("s", att)
    with pytest.raises(IncompatibleResume): SourceLifecycle.identify(s, {}, {"t": 2}, cp, OPTS)
    assert SourceLifecycle.identify(s, {}, {"t": 1}, cp, OPTS).identity == att.identity
    assert SourceLifecycle.identify(s, {}, {"t": 2}, cp, dict(OPTS, force=True)).identity != att.identity

def test_source_lifecycle_decide_replay_regenerate_run():
    s = CallableSource(lambda u, p, st: None, name="s"); cp = MemoryCheckpoint()
    ident = SourceLifecycle.identify(s, {}, {}, cp, OPTS)
    assert SourceLifecycle.decide(s, ident, cp, OPTS).tag == "RUN"
    cp.set_pending("s", Attempt(SourceState(), ident.identity, Record(ident.identity, Status.PARTIAL, None, None, Value.of([{"p": 1}], ident.identity)), None))
    assert SourceLifecycle.decide(s, ident, cp, OPTS).tag == "REPLAY"
    cp.set_pending("s", Attempt(SourceState(), ident.identity, Record(ident.identity, Status.COMPLETE, None, None, None), None))   # value not retained
    assert SourceLifecycle.decide(s, ident, cp, OPTS).tag == "REGENERATE"

def test_source_lifecycle_commit_gated():
    s = CallableSource(lambda u, p, st: None, name="s"); cp = MemoryCheckpoint()
    v = Value.of([{"p": "A"}], Identity.of("i"), Coverage.source({"A"}, {"A"}, set()))
    cp.set_pending("s", Attempt(SourceState(), Identity.of("i"), Record(Identity.of("i"), Status.COMPLETE, None, v.coverage, v), "A"))
    SourceLifecycle.commit(s, False, cp); assert cp.pending("s") is not None and cp.progress("s").cursor is None
    SourceLifecycle.commit(s, True, cp);  assert cp.pending("s") is None and cp.progress("s").cursor == "A"
