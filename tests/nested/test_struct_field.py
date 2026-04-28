"""Tests for struct field access."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def struct_df():
    return pl.DataFrame({
        "reaction": [
            {"emoji": "thumbs_up", "count": 5},
            {"emoji": "heart", "count": 3},
            {"emoji": "laugh", "count": 10},
        ],
    })


class TestStructField:
    def test_extract_string_field(self, struct_df):
        """struct.field() extracts a named field from a struct column."""
        expr = ma.col("reaction").struct.field("emoji")
        result = struct_df.with_columns(expr.compile(struct_df).alias("emoji"))
        assert result["emoji"].to_list() == ["thumbs_up", "heart", "laugh"]

    def test_extract_numeric_field(self, struct_df):
        """struct.field() extracts numeric fields."""
        expr = ma.col("reaction").struct.field("count")
        result = struct_df.with_columns(expr.compile(struct_df).alias("count"))
        assert result["count"].to_list() == [5, 3, 10]

    def test_chain_into_string_namespace(self, struct_df):
        """Extracted field chains into typed namespace."""
        expr = ma.col("reaction").struct.field("emoji").str.upper()
        result = struct_df.with_columns(expr.compile(struct_df).alias("upper_emoji"))
        assert result["upper_emoji"].to_list() == ["THUMBS_UP", "HEART", "LAUGH"]

    def test_aggregate_extracted_field(self, struct_df):
        """Extracted numeric field can be aggregated."""
        expr = ma.col("reaction").struct.field("count").sum()
        result = struct_df.select(expr.compile(struct_df).alias("total"))
        assert result["total"].to_list() == [18]

    def test_filter_on_extracted_field(self, struct_df):
        """Extracted field can be used in filter predicates."""
        expr = ma.col("reaction").struct.field("count") > ma.lit(4)
        result = struct_df.with_columns(expr.compile(struct_df).alias("popular"))
        assert result["popular"].to_list() == [True, False, True]
