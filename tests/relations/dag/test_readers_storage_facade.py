"""Tests for Task 12 — storage facade routing for remote paths.

All tests monkeypatch ``_facade_read_bytes`` to stub the facade — never hits
the network. The ``mountainash_utils_files`` package is not required at import
time because ``_facade_read_bytes`` uses a lazy import.
"""
from __future__ import annotations

import io

import polars as pl
import pytest

from mountainash.relations.dag.readers import read_resource_to_polars
from mountainash.typespec.datapackage import DataResource


def test_https_path_routed_through_facade(monkeypatch):
    fake_csv = b"a,b\n1,2\n"
    calls: list[str] = []

    def fake_read_bytes(path: str) -> bytes:
        calls.append(path)
        return fake_csv

    from mountainash.relations.dag.readers import csv as csv_reader

    monkeypatch.setattr(csv_reader, "_facade_read_bytes", fake_read_bytes)

    res = DataResource(name="t", path="https://example.com/t.csv", format="csv")
    df = read_resource_to_polars(res).collect()
    assert df["a"].to_list() == [1]
    assert calls == ["https://example.com/t.csv"]


def test_s3_path_routed_through_facade(monkeypatch):
    buf = io.BytesIO()
    pl.DataFrame({"x": [42]}).write_parquet(buf)
    fake_parquet = buf.getvalue()
    calls: list[str] = []

    def fake_read_bytes(path: str) -> bytes:
        calls.append(path)
        return fake_parquet

    from mountainash.relations.dag.readers import parquet as parquet_reader

    monkeypatch.setattr(parquet_reader, "_facade_read_bytes", fake_read_bytes)

    res = DataResource(name="t", path="s3://bucket/t.parquet", format="parquet")
    df = read_resource_to_polars(res).collect()
    assert df["x"].to_list() == [42]
    assert calls == ["s3://bucket/t.parquet"]


def test_r2_csv_routed_through_facade(monkeypatch):
    fake_csv = b"col\nhello\nworld\n"
    calls: list[str] = []

    def fake_read_bytes(path: str) -> bytes:
        calls.append(path)
        return fake_csv

    from mountainash.relations.dag.readers import csv as csv_reader

    monkeypatch.setattr(csv_reader, "_facade_read_bytes", fake_read_bytes)

    res = DataResource(name="t", path="r2://bucket/data.csv", format="csv")
    df = read_resource_to_polars(res).collect()
    assert df["col"].to_list() == ["hello", "world"]
    assert calls == ["r2://bucket/data.csv"]


def test_minio_json_routed_through_facade(monkeypatch):
    import json

    fake_json = json.dumps([{"k": 1}, {"k": 2}]).encode()
    calls: list[str] = []

    def fake_read_bytes(path: str) -> bytes:
        calls.append(path)
        return fake_json

    from mountainash.relations.dag.readers import json as json_reader

    monkeypatch.setattr(json_reader, "_facade_read_bytes", fake_read_bytes)

    res = DataResource(name="t", path="minio://bucket/data.json", format="json")
    df = read_resource_to_polars(res).collect()
    assert sorted(df["k"].to_list()) == [1, 2]
    assert calls == ["minio://bucket/data.json"]


def test_local_path_does_not_call_facade(monkeypatch, tmp_path):
    """Local paths must bypass _facade_read_bytes entirely."""
    p = tmp_path / "local.csv"
    p.write_text("n\n5\n")
    facade_calls: list[str] = []

    def must_not_be_called(path: str) -> bytes:
        facade_calls.append(path)
        raise AssertionError(f"facade called for local path: {path}")

    from mountainash.relations.dag.readers import csv as csv_reader

    monkeypatch.setattr(csv_reader, "_facade_read_bytes", must_not_be_called)

    res = DataResource(name="t", path=str(p), format="csv")
    df = read_resource_to_polars(res).collect()
    assert df["n"].to_list() == [5]
    assert facade_calls == []
