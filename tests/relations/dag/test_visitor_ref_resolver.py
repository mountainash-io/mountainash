"""Tests for UnifiedRelationVisitor ref_resolver and visit_resource_read_rel.

Tasks 13 and 14: ref_resolver keyword arg, visit_ref_rel, visit_resource_read_rel,
and _coerce_from_polars_lazy for all three backends.
"""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.relations.core.unified_visitor.relation_visitor import (
    UnifiedRelationVisitor,
)
from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    RefRelNode,
    ResourceReadRelNode,
)
from mountainash.relations.dag.errors import RelationDAGRequired
from mountainash.typespec.datapackage import DataResource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_polars_visitor(ref_resolver=None):
    """Build a UnifiedRelationVisitor wired to the Polars relation system."""
    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    rs = PolarsRelationSystem()
    return UnifiedRelationVisitor(rs, expression_visitor=None, ref_resolver=ref_resolver)


# ---------------------------------------------------------------------------
# Task 13: visit_ref_rel
# ---------------------------------------------------------------------------

def test_ref_without_resolver_raises():
    visitor = _make_polars_visitor()
    with pytest.raises(RelationDAGRequired):
        visitor.visit_ref_rel(RefRelNode(name="orders"))


def test_ref_with_resolver_returns_cached_value():
    cached = pl.DataFrame({"x": [1, 2]}).lazy()
    visitor = _make_polars_visitor(ref_resolver=lambda n: cached)
    result = visitor.visit_ref_rel(RefRelNode(name="orders"))
    assert result.collect()["x"].to_list() == [1, 2]


def test_ref_resolver_receives_correct_name():
    """The ref_resolver is called with the node's name string."""
    called_with = []
    cached = pl.DataFrame({"y": [10]}).lazy()

    def resolver(name):
        called_with.append(name)
        return cached

    visitor = _make_polars_visitor(ref_resolver=resolver)
    visitor.visit_ref_rel(RefRelNode(name="customers"))
    assert called_with == ["customers"]


# ---------------------------------------------------------------------------
# Task 13: visit_resource_read_rel (Polars path)
# ---------------------------------------------------------------------------

def test_resource_read_rel_loads_inline_data():
    visitor = _make_polars_visitor()
    res = DataResource(name="orders", data=[{"a": 1}, {"a": 2}], format="json")
    result = visitor.visit_resource_read_rel(ResourceReadRelNode(resource=res))
    df = result.collect() if isinstance(result, pl.LazyFrame) else result
    assert df["a"].to_list() == [1, 2]


def test_resource_read_rel_loads_csv_path(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,2\n3,4\n")
    visitor = _make_polars_visitor()
    res = DataResource(name="t", path=str(p), format="csv")
    result = visitor.visit_resource_read_rel(ResourceReadRelNode(resource=res))
    df = result.collect() if isinstance(result, pl.LazyFrame) else result
    assert df.shape == (2, 2)



# ---------------------------------------------------------------------------
# Task 13: existing positional constructor still works (no regression)
# ---------------------------------------------------------------------------

def test_existing_positional_constructor_unchanged():
    """UnifiedRelationVisitor(rs, expr_visitor) still works without ref_resolver."""
    from mountainash.relations.backends.relation_systems.polars import (
        PolarsRelationSystem,
    )
    rs = PolarsRelationSystem()
    visitor = UnifiedRelationVisitor(rs, None)
    assert visitor.ref_resolver is None
