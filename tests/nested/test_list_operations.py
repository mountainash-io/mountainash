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


# =============================================================================
# Batch 2a: Aggregation-like list ops
# =============================================================================

# Backends where all/any work: Polars + Ibis (Narwhals lacks these ops)
LIST_BACKENDS_POLARS_IBIS = [
    "polars",
    pytest.param(
        "narwhals-polars",
        marks=pytest.mark.xfail(strict=True, reason="Narwhals lacks list.all()/any()"),
    ),
    "ibis-duckdb",
]

# Backends where median works: Polars + Narwhals (Ibis lacks it)
LIST_BACKENDS_POLARS_NARWHALS = [
    "polars",
    "narwhals-polars",
    pytest.param(
        "ibis-duckdb",
        marks=pytest.mark.xfail(strict=True, reason="Ibis lacks array.median()"),
    ),
]

# Polars-only ops (both Narwhals and Ibis lack them)
LIST_BACKENDS_POLARS_ONLY = [
    "polars",
    pytest.param(
        "narwhals-polars",
        marks=pytest.mark.xfail(strict=True, reason="Narwhals lacks this list op"),
    ),
    pytest.param(
        "ibis-duckdb",
        marks=pytest.mark.xfail(strict=True, reason="Ibis lacks this array op"),
    ),
]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_IBIS)
class TestListAll:
    def test_all_true(self, backend_name, backend_factory, collect_expr):
        data = {"flags": [[True, True, True], [True, False], [True]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flags").list.all()
        result = collect_expr(df, expr)
        assert result == [True, False, True]

    def test_all_false(self, backend_name, backend_factory, collect_expr):
        data = {"flags": [[False, False], [True, True]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flags").list.all()
        result = collect_expr(df, expr)
        assert result == [False, True]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_IBIS)
class TestListAny:
    def test_any_mixed(self, backend_name, backend_factory, collect_expr):
        data = {"flags": [[False, False], [True, False], [True, True]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("flags").list.any()
        result = collect_expr(df, expr)
        assert result == [False, True, True]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_ONLY)
class TestListDropNulls:
    def test_drop_nulls(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[1, None, 2], [None, None], [3, 4]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.drop_nulls()
        result = collect_expr(df, expr)
        assert result == [[1, 2], [], [3, 4]]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_NARWHALS)
class TestListMedian:
    def test_median_odd(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[1, 2, 3], [10, 20, 30]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.median()
        result = collect_expr(df, expr)
        assert result == [2.0, 20.0]

    def test_median_even(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[1, 2, 3, 4], [10, 20]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.median()
        result = collect_expr(df, expr)
        assert result == [2.5, 15.0]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_ONLY)
class TestListStd:
    def test_std_default_ddof(self, backend_name, backend_factory, collect_expr):
        import math
        data = {"vals": [[2, 4, 4, 4, 5, 5, 7, 9]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.std()
        result = collect_expr(df, expr)
        assert math.isclose(result[0], 2.138089935, rel_tol=1e-5)

    def test_std_ddof_zero(self, backend_name, backend_factory, collect_expr):
        import math
        data = {"vals": [[2, 4, 4, 4, 5, 5, 7, 9]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.std(ddof=0)
        result = collect_expr(df, expr)
        assert math.isclose(result[0], 2.0, rel_tol=1e-5)


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_ONLY)
class TestListVar:
    def test_var_default_ddof(self, backend_name, backend_factory, collect_expr):
        import math
        data = {"vals": [[2, 4, 4, 4, 5, 5, 7, 9]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.var()
        result = collect_expr(df, expr)
        assert math.isclose(result[0], 4.571428571, rel_tol=1e-5)

    def test_var_ddof_zero(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[2, 4, 4, 4, 5, 5, 7, 9]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.var(ddof=0)
        result = collect_expr(df, expr)
        assert result[0] == 4.0


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_ONLY)
class TestListNUnique:
    def test_n_unique(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[1, 2, 2, 3], [5, 5, 5], [10]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.n_unique()
        result = collect_expr(df, expr)
        assert result == [3, 1, 1]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_ONLY)
class TestListCountMatches:
    def test_count_matches_literal(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[1, 2, 1, 3], [1, 1, 1], [2, 3]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.count_matches(1)
        result = collect_expr(df, expr)
        assert result == [2, 3, 0]


@pytest.mark.parametrize("backend_name", LIST_BACKENDS_POLARS_ONLY)
class TestListItem:
    def test_item_first(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[10, 20, 30], [40, 50]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.item(index=0)
        result = collect_expr(df, expr)
        assert result == [10, 40]

    def test_item_oob_returns_null(self, backend_name, backend_factory, collect_expr):
        data = {"vals": [[10, 20], [30]]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("vals").list.item(index=5)
        result = collect_expr(df, expr)
        assert result[0] is None
        assert result[1] is None
