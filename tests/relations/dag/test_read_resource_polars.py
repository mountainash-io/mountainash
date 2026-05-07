"""Tests for Polars read_resource — format detection + all reader paths."""
from __future__ import annotations

import json

import polars as pl
import pytest

from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
    MountainashPolarsExtensionRelationSystem,
)
from mountainash.relations.dag.errors import UnsupportedResourceFormat
from mountainash.typespec.datapackage import DataResource, TableDialect


@pytest.fixture()
def polars_ext() -> MountainashPolarsExtensionRelationSystem:
    return MountainashPolarsExtensionRelationSystem()


def test_inline_list_of_dicts(polars_ext):
    res = DataResource(name="t", data=[{"a": 1}, {"a": 2}], format="json")
    lf = polars_ext.read_resource(res)
    assert isinstance(lf, pl.LazyFrame)
    assert lf.collect()["a"].to_list() == [1, 2]


def test_csv_local(polars_ext, tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,2\n3,4\n")
    res = DataResource(name="t", path=str(p), format="csv")
    df = polars_ext.read_resource(res).collect()
    assert df.shape == (2, 2)


def test_csv_with_dialect(polars_ext, tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a;b\n1;2\n")
    res = DataResource(
        name="t", path=str(p), format="csv",
        dialect=TableDialect(delimiter=";"),
    )
    assert polars_ext.read_resource(res).collect().shape == (1, 2)


def test_parquet_local(polars_ext, tmp_path):
    p = tmp_path / "t.parquet"
    pl.DataFrame({"a": [1, 2]}).write_parquet(p)
    res = DataResource(name="t", path=str(p), format="parquet")
    df = polars_ext.read_resource(res).collect()
    assert df["a"].to_list() == [1, 2]


def test_json_local(polars_ext, tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps([{"x": 10}, {"x": 20}]))
    res = DataResource(name="t", path=str(p), format="json")
    df = polars_ext.read_resource(res).collect()
    assert sorted(df["x"].to_list()) == [10, 20]


def test_format_detection_from_extension(polars_ext, tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("a\n1\n")
    res = DataResource(name="t", path=str(p))
    df = polars_ext.read_resource(res).collect()
    assert df.shape == (1, 1)


def test_format_detection_from_parquet_extension(polars_ext, tmp_path):
    p = tmp_path / "t.parquet"
    pl.DataFrame({"z": [99]}).write_parquet(p)
    res = DataResource(name="t", path=str(p))
    df = polars_ext.read_resource(res).collect()
    assert df["z"].to_list() == [99]


def test_multi_file_csv_concat(polars_ext, tmp_path):
    a = tmp_path / "a.csv"
    a.write_text("x\n1\n")
    b = tmp_path / "b.csv"
    b.write_text("x\n2\n")
    res = DataResource(name="t", path=[str(a), str(b)], format="csv")
    df = polars_ext.read_resource(res).collect()
    assert sorted(df["x"].to_list()) == [1, 2]


def test_multi_file_parquet_concat(polars_ext, tmp_path):
    a = tmp_path / "a.parquet"
    b = tmp_path / "b.parquet"
    pl.DataFrame({"v": [1]}).write_parquet(a)
    pl.DataFrame({"v": [2]}).write_parquet(b)
    res = DataResource(name="t", path=[str(a), str(b)], format="parquet")
    df = polars_ext.read_resource(res).collect()
    assert sorted(df["v"].to_list()) == [1, 2]


def test_unknown_format_raises(polars_ext):
    res = DataResource(name="t", path="t.weird", format="weird")
    with pytest.raises(UnsupportedResourceFormat, match="weird"):
        polars_ext.read_resource(res)
