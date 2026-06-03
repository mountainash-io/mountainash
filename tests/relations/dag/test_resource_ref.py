"""Tests for ResourceRef wrapper (Task 15)."""
from __future__ import annotations

import pytest
from mountainash.relations.dag.resource_ref import ResourceRef
from mountainash.typespec.datapackage import DataResource


def test_tabular_resource_ref(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a\n1\n")
    res = DataResource(name="t", path=str(p), type="table", format="csv")
    ref = ResourceRef(res)
    assert ref.is_tabular
    assert ref.read_bytes() == p.read_bytes()
    rel = ref.relation()
    assert rel is not None


def test_non_tabular_resource_ref(tmp_path):
    p = tmp_path / "logo.png"
    p.write_bytes(b"\x89PNG...")
    res = DataResource(name="logo", path=str(p), format="png")
    ref = ResourceRef(res)
    assert not ref.is_tabular
    assert ref.read_bytes() == b"\x89PNG..."
    with pytest.raises(ValueError, match="not tabular"):
        ref.relation()


def test_inline_data_cannot_read_bytes():
    res = DataResource(name="t", data=[{"a": 1}], format="json")
    ref = ResourceRef(res)
    with pytest.raises(ValueError, match="inline"):
        ref.read_bytes()


def test_resource_ref_import_paths_share_same_class():
    from mountainash import ResourceRef as PublicResourceRef
    from mountainash.core.resource_ref import ResourceRef as CoreResourceRef
    from mountainash.relations.dag.resource_ref import ResourceRef as DagResourceRef

    assert PublicResourceRef is CoreResourceRef
    assert DagResourceRef is CoreResourceRef


def test_resource_ref_relation_compatibility_method(tmp_path):
    from mountainash.core.resource_ref import ResourceRef
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        ResourceReadRelNode,
    )

    p = tmp_path / "orders.csv"
    p.write_text("id\n1\n")
    res = DataResource(name="orders", path=str(p), type="table", format="csv")

    rel = ResourceRef(res).relation()

    assert isinstance(rel._node, ResourceReadRelNode)
