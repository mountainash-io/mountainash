"""Tests for list operations."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError

LIST_BACKENDS = [
    "polars",
    "narwhals-polars",
    "ibis-duckdb",
]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListAggregates:
    def test_list_sum(self, backend_name, backend_factory, collect_expr):
        data = {"scores": [[10, 20, 30], [5, 15], [100]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("scores").list.sum()
        result = collect_expr(df, expr)
        assert result == [60, 20, 100]

    def test_list_min(self, backend_name, backend_factory, collect_expr):
        data = {"scores": [[10, 20, 30], [5, 15], [100]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("scores").list.min()
        result = collect_expr(df, expr)
        assert result == [10, 5, 100]

    def test_list_max(self, backend_name, backend_factory, collect_expr):
        data = {"scores": [[10, 20, 30], [5, 15], [100]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("scores").list.max()
        result = collect_expr(df, expr)
        assert result == [30, 15, 100]

    def test_list_mean(self, backend_name, backend_factory, collect_expr):
        data = {"scores": [[10, 20, 30], [5, 15], [100]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("scores").list.mean()
        result = collect_expr(df, expr)
        assert result == [20.0, 10.0, 100.0]

    def test_list_len(self, backend_name, backend_factory, collect_expr):
        data = {"scores": [[10, 20, 30], [5, 15], [100]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("scores").list.len()
        result = collect_expr(df, expr)
        assert result == [3, 2, 1]


@pytest.mark.parametrize("backend_name", [
    "polars",
    pytest.param("narwhals-polars", marks=pytest.mark.xfail(
        strict=True,
        reason="Narwhals list.contains() rejects compiled Expr arguments (known-divergences.md #9)",
    )),
    "ibis-duckdb",
])
class TestListContains:
    def test_contains_literal(self, backend_name, backend_factory, collect_expr):
        data = {"tags": [["python", "rust"], ["python"], ["go", "rust", "python"]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("tags").list.contains("python")
        result = collect_expr(df, expr)
        assert result == [True, True, True]

    def test_contains_literal_miss(self, backend_name, backend_factory, collect_expr):
        data = {"tags": [["python", "rust"], ["python"], ["go", "rust", "python"]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("tags").list.contains("java")
        result = collect_expr(df, expr)
        assert result == [False, False, False]


@pytest.mark.parametrize("backend_name", [
    "polars",
    "narwhals-polars",
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
        strict=True,
        reason="Ibis ArrayValue.sort() has no descending parameter (known-divergences.md)",
    )),
])
class TestListSortDescending:
    def test_sort_descending(self, backend_name, backend_factory, collect_expr):
        data = {"scores": [[10, 20, 30], [5, 15], [100]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("scores").list.sort(descending=True)
        result = collect_expr(df, expr)
        assert result == [[30, 20, 10], [15, 5], [100]]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListSortAscending:
    def test_sort_ascending(self, backend_name, backend_factory, collect_expr):
        data = {"scores": [[30, 10, 20], [15, 5], [100]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("scores").list.sort()
        result = collect_expr(df, expr)
        assert result == [[10, 20, 30], [5, 15], [100]]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListUnique:
    def test_unique(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[1, 2, 2, 3], [5, 5, 5]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.unique()
        result = collect_expr(df, expr)
        assert sorted(result[0]) == [1, 2, 3]
        assert sorted(result[1]) == [5]


class TestListChaining:
    def test_sum_gt(self):
        """Chaining: list aggregate result used in comparison."""
        df = pl.DataFrame({"scores": [[10, 20, 30], [5, 15], [100]]})
        expr = ma.col("scores").list.sum() > ma.lit(50)
        result = df.with_columns(expr.compile(df).alias("big"))
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


# =============================================================================
# D6: list.explode()
# =============================================================================


@pytest.mark.parametrize("backend_name", [
    "polars",
    pytest.param("narwhals-polars", marks=pytest.mark.xfail(
        strict=True,
        reason="Narwhals has no list.explode() equivalent (known-divergences.md)",
    )),
    "ibis-duckdb",
])
class TestListExplode:
    def test_explode_basic(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[1, 2, 3], [4, 5]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.explode()
        result = collect_expr(df, expr)
        assert result == [1, 2, 3, 4, 5]


# =============================================================================
# D7: list.join(separator)
# =============================================================================


@pytest.mark.parametrize("backend_name", [
    "polars",
    pytest.param("narwhals-polars", marks=pytest.mark.xfail(
        strict=True,
        reason="Narwhals has no list.join() equivalent (known-divergences.md)",
    )),
    "ibis-duckdb",
])
class TestListJoin:
    def test_join_comma(self, backend_name, backend_factory, collect_expr):
        data = {"tags": [["a", "b", "c"], ["x", "y"]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("tags").list.join(",")
        result = collect_expr(df, expr)
        assert result == ["a,b,c", "x,y"]

    def test_join_space(self, backend_name, backend_factory, collect_expr):
        data = {"words": [["hello", "world"], ["foo"]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("words").list.join(" ")
        result = collect_expr(df, expr)
        assert result == ["hello world", "foo"]


# =============================================================================
# D8: list.get(index), list.first(), list.last()
# =============================================================================


@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListGet:
    def test_get_first(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[10, 20, 30], [40, 50]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.get(0)
        result = collect_expr(df, expr)
        assert result == [10, 40]

    def test_get_middle(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[10, 20, 30], [40, 50, 60]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.get(1)
        result = collect_expr(df, expr)
        assert result == [20, 50]

    def test_first_sugar(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[10, 20, 30], [40, 50]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.first()
        result = collect_expr(df, expr)
        assert result == [10, 40]


@pytest.mark.parametrize("backend_name", [
    "polars",
    pytest.param("narwhals-polars", marks=pytest.mark.xfail(
        strict=True,
        reason="Narwhals list.get() does not support negative indices",
    )),
    "ibis-duckdb",
])
class TestListGetNegative:
    def test_get_last(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[10, 20, 30], [40, 50]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.get(-1)
        result = collect_expr(df, expr)
        assert result == [30, 50]

    def test_last_sugar(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[10, 20, 30], [40, 50]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.last()
        result = collect_expr(df, expr)
        assert result == [30, 50]


class TestNarwhalsExplodeJoinGuard:
    """Narwhals must raise BackendCapabilityError for unsupported list ops."""

    def test_narwhals_explode_raises(self):
        import narwhals as nw
        df = nw.from_native(pl.DataFrame({"vals": [[1, 2]]}), eager_only=True)
        expr = ma.col("vals").list.explode()
        with pytest.raises(BackendCapabilityError, match="explode"):
            expr.compile(df)

    def test_narwhals_join_raises(self):
        import narwhals as nw
        df = nw.from_native(pl.DataFrame({"tags": [["a", "b"]]}), eager_only=True)
        expr = ma.col("tags").list.join(",")
        with pytest.raises(BackendCapabilityError, match="join"):
            expr.compile(df)
