# tests/pipelines/core/test_digest.py
import polars as pl, pytest
import mountainash as ma
from mountainash.relations.dag import RelationDAG
from mountainash.pipelines.core.digest import structural_digest
from mountainash.pipelines.errors import UnhashableIdentityInput


def _t(threshold):
    t = RelationDAG()
    t.add("big", t.ref("orders").filter(ma.col("amt").gt(threshold)))
    t.add("out", t.ref("big").filter(ma.col("id").gt(1)))
    return t

def test_digest_stable_and_sensitive_to_nested_predicate():
    assert structural_digest(_t(15), "out", {"orders"}) == structural_digest(_t(15), "out", {"orders"})
    assert structural_digest(_t(15), "out", {"orders"}) != structural_digest(_t(99), "out", {"orders"})

def test_digest_restart_stable_pin():
    assert structural_digest(_t(15), "out", {"orders"}) == "32debaef1778d7fe75ea5ddb0544798a"   # a change to the walker must consciously update this pin

def test_digest_refuses_unbound_native_leaf():
    t = RelationDAG(); t.source("raw", pl.DataFrame({"a": [1]})); t.add("out", t.ref("raw"))
    with pytest.raises(UnhashableIdentityInput):
        structural_digest(t, "out", set())
