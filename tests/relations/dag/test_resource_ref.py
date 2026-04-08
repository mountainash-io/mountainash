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
