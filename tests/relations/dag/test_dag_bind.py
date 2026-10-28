# tests/relations/dag/test_dag_bind.py
import polars as pl, pytest
import mountainash as ma
from mountainash.relations.dag import RelationDAG
from mountainash.graph.errors import DuplicateNodeError


def _template():
    t = RelationDAG()
    t.add("big", t.ref("orders").filter(ma.col("amt").gt(15)))
    t.add("out", t.ref("big").select("id"))
    return t


def test_bind_registers_sources_and_leaves_template_untouched(backend_name):
    from fixtures.backend_registry import REGISTRY
    t = _template()
    frame = REGISTRY[backend_name].build({"id": [1, 2, 3], "amt": [10, 20, 30]}, "orders_bind")   # builder contract is (data, table_name)
    e = t.bind(orders=frame)
    assert "orders" in e.relations and "orders" not in t.relations
    assert ("orders", "big") in e.dependency_edges and ("big", "out") in e.dependency_edges
    assert sorted(ma.relation(e.collect("out")).collect()["id"].to_list()) == [2, 3]


def test_bind_twice_independent(backend_name):
    from fixtures.backend_registry import REGISTRY
    t = _template()
    e1 = t.bind(orders=REGISTRY[backend_name].build({"id": [1], "amt": [99]}, "o1"))
    e2 = t.bind(orders=REGISTRY[backend_name].build({"id": [7], "amt": [99]}, "o2"))
    assert ma.relation(e1.collect("out")).collect()["id"].to_list() == [1] and ma.relation(e2.collect("out")).collect()["id"].to_list() == [7]


def test_bind_duplicate_name_refused():
    t = _template()
    with pytest.raises(DuplicateNodeError):
        t.bind(big=pl.DataFrame({"id": [1]}))


def test_bind_copies_constraints_and_assets():
    from mountainash.typespec.spec import ForeignKey, ForeignKeyReference
    t = _template()
    t.add("child", t.ref("out").select("id"))
    t.add_constraint("child", ForeignKey(fields=["id"], reference=ForeignKeyReference(resource="out", fields=["id"])))
    e = t.bind(orders=pl.DataFrame({"id": [1], "amt": [99]}))
    assert ("out", "child") in e.constraint_edges and e.constraints_for("child") == t.constraints_for("child")


def test_public_graph_attributes_are_read_only():
    t = _template()
    with pytest.raises(AttributeError):
        t.relations = {}
