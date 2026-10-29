# tests/pipelines/units/test_source_unit.py
import pytest
from mountainash.pipelines.units.source import CallableSource
from mountainash.pipelines.core.values import Identity, SourceState, SourceResult, Value, Coverage, RunContext

@pytest.mark.cell("unit:CallableSource")
@pytest.mark.cell("unit:SourceUnit")
def test_callable_source_receives_upstream_params_state():
    seen = {}
    def fetch(upstream, params, state):
        seen.update(upstream=upstream, params=params, state=state)
        return SourceResult(Value.of([{"a": 1}], Identity.of("t"), Coverage.source({"A"}, {"A"}, set())), "A")
    s = CallableSource(fetch, name="s", depends_on=("ref",))
    ref = Value.of([{"r": 1}], Identity.of("r"))
    st = SourceState("Z", frozenset({"Q"}), frozenset())
    res = s.run({"ref": ref}, RunContext({"k": 1}, st, {}, "p", "s", "r"))
    assert seen == {"upstream": {"ref": ref}, "params": {"k": 1}, "state": st} and res.next_cursor == "A"

@pytest.mark.cell("unit:CallableSource")
@pytest.mark.cell("unit:SourceUnit")
def test_source_identity_includes_state():
    s = CallableSource(lambda u, p, st: None, name="s")
    a = s.identity({}, {}, SourceState(None, frozenset(), frozenset()))
    b = s.identity({}, {}, SourceState("A", frozenset(), frozenset()))
    c = s.identity({}, {}, SourceState(None, frozenset({"A"}), frozenset()))
    assert len({a, b, c}) == 3
