# tests/pipelines/units/sinks/test_sink_modes.py — coverage rules independent of destination
import pytest
from mountainash.pipelines.core.values import *
from mountainash.pipelines.units.sinks.base import SinkUnit, WriteMode
from mountainash.pipelines.errors import IncompleteCoverage

class Mem(SinkUnit):
    def __init__(self, mode, **kw): super().__init__(name="k", depends_on=("s",), mode=mode, **kw); self.writes = []
    def destination(self): return "mem://k"
    def write(self, value): self.writes.append(value); return LocatorReference("mem://k", value.record_count())

def _v(cov): return Value.of([{"p": 1, "k": 1}], Identity.of("i"), cov)
def _ctx(): return RunContext({}, None, {}, "p", "k", "r")

def test_replace_refuses_incomplete_even_through_marker():
    with pytest.raises(IncompleteCoverage): Mem(WriteMode.REPLACE).run({"s": _v(Coverage.partial_marker())}, _ctx())
    with pytest.raises(IncompleteCoverage): Mem(WriteMode.REPLACE).run({"s": _v(Coverage.source({"A"}, set(), {"A"}))}, _ctx())
    assert Mem(WriteMode.REPLACE).run({"s": _v(None)}, _ctx()).locator == "mem://k"

def test_replace_partition_requires_partition_sets():
    with pytest.raises(IncompleteCoverage): Mem(WriteMode.REPLACE_PARTITION, partition_columns=("p",)).run({"s": _v(Coverage.partial_marker())}, _ctx())
    Mem(WriteMode.REPLACE_PARTITION, partition_columns=("p",)).run({"s": _v(Coverage.source({1}, {1}, set()))}, _ctx())

def test_append_and_upsert_accept_any_coverage():
    for m in (WriteMode.APPEND, WriteMode.UPSERT):
        Mem(m, keys=("k",)).run({"s": _v(Coverage.partial_marker())}, _ctx())
