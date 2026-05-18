"""Tests for struct field access."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma

STRUCT_BACKENDS = [
    "polars",
    "narwhals-polars",
    "ibis-duckdb",
]


@pytest.mark.parametrize("backend_name", STRUCT_BACKENDS)
class TestStructField:
    def test_extract_string_field(self, backend_name, backend_factory, collect_expr):
        data = {"reaction": [{"emoji": "thumbs_up", "count": 5}, {"emoji": "heart", "count": 3}]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("reaction").struct.field("emoji")
        result = collect_expr(df, expr)
        assert result == ["thumbs_up", "heart"]

    def test_extract_numeric_field(self, backend_name, backend_factory, collect_expr):
        data = {"reaction": [{"emoji": "thumbs_up", "count": 5}, {"emoji": "heart", "count": 3}]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("reaction").struct.field("count")
        result = collect_expr(df, expr)
        assert result == [5, 3]


class TestStructFieldChaining:
    """Chaining and aggregation — Polars-only (struct literal creation is Polars-native)."""

    def test_chain_into_string_namespace(self):
        df = pl.DataFrame({"reaction": [{"emoji": "thumbs_up"}, {"emoji": "heart"}]})
        expr = ma.col("reaction").struct.field("emoji").str.upper()
        result = df.with_columns(expr.compile(df).alias("upper_emoji"))
        assert result["upper_emoji"].to_list() == ["THUMBS_UP", "HEART"]

    def test_aggregate_extracted_field(self):
        df = pl.DataFrame({"reaction": [{"count": 5}, {"count": 3}, {"count": 10}]})
        expr = ma.col("reaction").struct.field("count").sum()
        result = df.select(expr.compile(df).alias("total"))
        assert result["total"].to_list() == [18]

    def test_filter_on_extracted_field(self):
        df = pl.DataFrame({"reaction": [{"count": 5}, {"count": 3}, {"count": 10}]})
        expr = ma.col("reaction").struct.field("count") > ma.lit(4)
        result = df.with_columns(expr.compile(df).alias("popular"))
        assert result["popular"].to_list() == [True, False, True]
