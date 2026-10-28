# tests/pipelines/units/test_dag_unit.py
import pytest
import mountainash as ma
from mountainash.relations.dag import RelationDAG
from mountainash.pipelines.core.values import Identity, Value, ValueKind
from mountainash.pipelines.units.dag import DagUnit
from mountainash.pipelines.errors import UnsupportedValueKind


def _t():
    t = RelationDAG(); t.add("out", t.ref("orders").filter(ma.col("amt").gt(15))); return t

def _ctx():
    from mountainash.pipelines.core.values import RunContext
    return RunContext({}, None, {}, "p", "dag", "r")

ORDERS = {"id": [1, 2, 3], "amt": [10, 20, 30]}

@pytest.mark.cell("unit:DagUnit")
def test_dag_unit_native_handoff_zero_export(backend_name):
    from unittest import mock
    from fixtures.backend_registry import REGISTRY
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system
    from mountainash.core.backend_detection import native_identity
    frame = REGISTRY[backend_name].build(ORDERS, "orders_handoff")       # schema-matched frame; builder contract is (data, table_name) (F22/F34)
    sys_cls = get_relation_system(native_identity(frame).family)
    u = DagUnit(_t(), "out", name="dag", inputs={"orders": "orders"})
    with mock.patch.object(sys_cls, "export", side_effect=AssertionError("export called")):
        out = u.run({"orders": Value.of(frame, Identity.of("x"))}, _ctx())
    v = Value.of(out, Identity.of("y"))
    assert v.kind is ValueKind.TABULAR and ma.relation(out).count_rows() == 2

@pytest.mark.cell("unit:DagUnit")
def test_dag_unit_named_index_pandas_handoff():                        # Review Focus #1 through the handoff
    import narwhals as nw, pandas as pd
    df = pd.DataFrame({"id": [1, 2], "amt": [10, 99]}, index=pd.Index(["x", "y"], name="k"))
    u = DagUnit(_t(), "out", name="dag", inputs={"orders": "orders"})
    out = u.run({"orders": Value.of(nw.from_native(df), Identity.of("x"))}, _ctx())
    v = Value.of(out, Identity.of("y"))
    assert v.kind is ValueKind.TABULAR and v.location.dialect == "narwhals-pandas" and ma.relation(out).count_rows() == 1
    assert type(nw.to_native(out)).__module__.startswith("pandas")           # native carrier preserved through the handoff (no Arrow/Polars hop)
    frame = nw.from_native(df); assert DagUnit.adapt(Value.of(frame, Identity.of("x"))) is frame      # TABULAR adaptation is the identity function

@pytest.mark.cell("unit:DagUnit")
def test_dag_unit_runs_twice_with_different_inputs_and_after_failure(backend_name):
    from fixtures.backend_registry import REGISTRY
    B = lambda data, n: Value.of(REGISTRY[backend_name].build(data, n), Identity.of(n))   # noqa: E731
    u = DagUnit(_t(), "out", name="dag", inputs={"orders": "orders"})
    a = u.run({"orders": B({"id": [1], "amt": [99]}, "o1")}, _ctx()); b = u.run({"orders": B({"id": [2], "amt": [99]}, "o2")}, _ctx())
    assert ma.relation(a).collect()["id"].to_list() == [1] and ma.relation(b).collect()["id"].to_list() == [2]
    with pytest.raises(Exception):
        ma.relation(u.run({"orders": B({"id": [1]}, "o3")}, _ctx())).collect()           # missing column → fails at run (eager) or materialisation (lazy)
    assert ma.relation(u.run({"orders": B({"id": [3], "amt": [99]}, "o4")}, _ctx())).collect()["id"].to_list() == [3]   # fresh bind after failure

@pytest.mark.cell("unit:DagUnit")
def test_dag_unit_identity_includes_target_name_and_target():
    t = RelationDAG(); t.add("a", t.ref("l").select("id")); t.add("b", t.ref("l").select("id"))
    assert DagUnit(t, "a", name="d", inputs={"up": "l"}).identity({"up": Identity.of("u")}, {}, None) != DagUnit(t, "b", name="d", inputs={"up": "l"}).identity({"up": Identity.of("u")}, {}, None)
    assert DagUnit(t, "a", name="d", inputs={"up": "l"}, target="polars").identity({"up": Identity.of("u")}, {}, None) != DagUnit(t, "a", name="d", inputs={"up": "l"}, target="ibis-duckdb").identity({"up": Identity.of("u")}, {}, None)

@pytest.mark.cell("unit:DagUnit")
def test_dag_unit_records_via_rows_to_arrow_sparse():
    u = DagUnit(_t(), "out", name="dag", inputs={"orders": "orders"})
    out = u.run({"orders": Value.of([{"id": 1, "amt": 10}, {"id": 2}], Identity.of("x"))}, _ctx())
    assert ma.relation(out).collect().shape[0] == 0           # amt null → filtered out, no KeyError on sparse row

@pytest.mark.cell("unit:DagUnit")
@pytest.mark.cell("kind:REFERENCE")
@pytest.mark.cell("kind:OPAQUE")
def test_dag_unit_refuses_reference_and_passes_opaque():
    from dataclasses import dataclass
    from mountainash.pipelines.core.values import LocatorReference
    u = DagUnit(_t(), "out", name="dag", inputs={"orders": "orders"})
    with pytest.raises(UnsupportedValueKind):
        u.run({"orders": Value.of(LocatorReference("mem://x", 1), Identity.of("x"))}, _ctx())
    @dataclass
    class Row: id: int; amt: int
    out = u.run({"orders": Value.of([Row(1, 20)], Identity.of("x"))}, _ctx())      # existing Python-model ingress
    assert ma.relation(out).collect().shape[0] == 1

@pytest.mark.cell("unit:DagUnit")
def test_dag_unit_identity_includes_inputs_mapping():
    t = RelationDAG(); t.add("out", t.ref("l").select("id")); t.add("r", t.ref("l"))
    a = DagUnit(t, "out", name="d", inputs={"up": "l"}).identity({"up": Identity.of("u")}, {}, None)
    b = DagUnit(t, "out", name="d", inputs={"up": "r"}).identity({"up": Identity.of("u")}, {}, None)
    assert a != b
