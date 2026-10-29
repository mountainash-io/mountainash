"""Tests for Task 11 — format-dispatched resource readers (local paths + inline)."""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
    MountainashPolarsExtensionRelationSystem,
)
from mountainash.relations.dag.errors import UnsupportedResourceFormat
from mountainash.typespec.datapackage import DataResource, TableDialect

_polars_ext = MountainashPolarsExtensionRelationSystem()


def read_resource_to_polars(res):
    """Compatibility shim — delegates to Polars backend's read_resource."""
    return _polars_ext.read_resource(res)


def test_inline_list_of_dicts():
    res = DataResource(name="t", data=[{"a": 1}, {"a": 2}], format="json")
    df = read_resource_to_polars(res).collect()
    assert df["a"].to_list() == [1, 2]


def test_csv_path(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,2\n3,4\n")
    res = DataResource(name="t", path=str(p), format="csv")
    df = read_resource_to_polars(res).collect()
    assert df.shape == (2, 2)


def test_csv_with_dialect(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a;b\n1;2\n")
    res = DataResource(
        name="t",
        path=str(p),
        format="csv",
        dialect=TableDialect(delimiter=";"),
    )
    assert read_resource_to_polars(res).collect().shape == (1, 2)


def test_multi_file_path_concat(tmp_path):
    a = tmp_path / "a.csv"
    a.write_text("x\n1\n")
    b = tmp_path / "b.csv"
    b.write_text("x\n2\n")
    res = DataResource(name="t", path=[str(a), str(b)], format="csv")
    df = read_resource_to_polars(res).collect()
    assert sorted(df["x"].to_list()) == [1, 2]


def test_parquet_path(tmp_path):
    p = tmp_path / "t.parquet"
    pl.DataFrame({"a": [1, 2]}).write_parquet(p)
    res = DataResource(name="t", path=str(p), format="parquet")
    df = read_resource_to_polars(res).collect()
    assert df["a"].to_list() == [1, 2]


def test_json_path(tmp_path):
    p = tmp_path / "t.json"
    import json

    p.write_text(json.dumps([{"x": 10}, {"x": 20}]))
    res = DataResource(name="t", path=str(p), format="json")
    df = read_resource_to_polars(res).collect()
    assert sorted(df["x"].to_list()) == [10, 20]


def test_format_detection_from_extension(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a\n1\n")
    res = DataResource(name="t", path=str(p))  # no format declared
    df = read_resource_to_polars(res).collect()
    assert df.shape == (1, 1)


def test_format_detection_from_parquet_extension(tmp_path):
    p = tmp_path / "t.parquet"
    pl.DataFrame({"z": [99]}).write_parquet(p)
    res = DataResource(name="t", path=str(p))  # no format declared
    df = read_resource_to_polars(res).collect()
    assert df["z"].to_list() == [99]


def test_unknown_format_raises():
    res = DataResource(name="t", path="t.weird", format="weird")
    with pytest.raises(UnsupportedResourceFormat, match="weird"):
        read_resource_to_polars(res)


def test_multi_file_parquet_concat(tmp_path):
    a = tmp_path / "a.parquet"
    b = tmp_path / "b.parquet"
    pl.DataFrame({"v": [1]}).write_parquet(a)
    pl.DataFrame({"v": [2]}).write_parquet(b)
    res = DataResource(name="t", path=[str(a), str(b)], format="parquet")
    df = read_resource_to_polars(res).collect()
    assert sorted(df["v"].to_list()) == [1, 2]
