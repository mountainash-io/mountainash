"""Tests for list operations."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError


@pytest.fixture
def list_df():
    return pl.DataFrame({
        "scores": [[10, 20, 30], [5, 15], [100]],
        "tags": [["python", "rust"], ["python"], ["go", "rust", "python"]],
    })


class TestListAggregates:
    def test_list_sum(self, list_df):
        expr = ma.col("scores").list.sum()
        result = list_df.with_columns(expr.compile(list_df).alias("total"))
        assert result["total"].to_list() == [60, 20, 100]

    def test_list_min(self, list_df):
        expr = ma.col("scores").list.min()
        result = list_df.with_columns(expr.compile(list_df).alias("lo"))
        assert result["lo"].to_list() == [10, 5, 100]

    def test_list_max(self, list_df):
        expr = ma.col("scores").list.max()
        result = list_df.with_columns(expr.compile(list_df).alias("hi"))
        assert result["hi"].to_list() == [30, 15, 100]

    def test_list_mean(self, list_df):
        expr = ma.col("scores").list.mean()
        result = list_df.with_columns(expr.compile(list_df).alias("avg"))
        assert result["avg"].to_list() == [20.0, 10.0, 100.0]

    def test_list_len(self, list_df):
        expr = ma.col("scores").list.len()
        result = list_df.with_columns(expr.compile(list_df).alias("n"))
        assert result["n"].to_list() == [3, 2, 1]


class TestListContains:
    def test_contains_literal(self, list_df):
        expr = ma.col("tags").list.contains("python")
        result = list_df.with_columns(expr.compile(list_df).alias("has_py"))
        assert result["has_py"].to_list() == [True, True, True]

    def test_contains_literal_miss(self, list_df):
        expr = ma.col("tags").list.contains("java")
        result = list_df.with_columns(expr.compile(list_df).alias("has_java"))
        assert result["has_java"].to_list() == [False, False, False]


class TestListSort:
    def test_sort_ascending(self, list_df):
        expr = ma.col("scores").list.sort()
        result = list_df.with_columns(expr.compile(list_df).alias("sorted"))
        assert result["sorted"].to_list() == [[10, 20, 30], [5, 15], [100]]

    def test_sort_descending(self, list_df):
        expr = ma.col("scores").list.sort(descending=True)
        result = list_df.with_columns(expr.compile(list_df).alias("sorted"))
        assert result["sorted"].to_list() == [[30, 20, 10], [15, 5], [100]]


class TestListUnique:
    def test_unique(self):
        df = pl.DataFrame({"vals": [[1, 2, 2, 3], [5, 5, 5]]})
        expr = ma.col("vals").list.unique()
        result = df.with_columns(expr.compile(df).alias("uniq"))
        uniq_lists = result["uniq"].to_list()
        assert sorted(uniq_lists[0]) == [1, 2, 3]
        assert sorted(uniq_lists[1]) == [5]


class TestListChaining:
    def test_sum_gt(self, list_df):
        """Chaining: list aggregate result used in comparison."""
        expr = ma.col("scores").list.sum() > ma.lit(50)
        result = list_df.with_columns(expr.compile(list_df).alias("big"))
        assert result["big"].to_list() == [True, False, True]


class TestIbisDescendingSortGuard:
    def test_ibis_descending_raises(self):
        """Ibis must raise BackendCapabilityError for descending list sort."""
        import ibis

        con = ibis.duckdb.connect()
        t = con.create_table("_test_list_sort", {"scores": [[3, 1, 2]]})

        expr = ma.col("scores").list.sort(descending=True)
        with pytest.raises(BackendCapabilityError, match="descending"):
            expr.compile(t)
