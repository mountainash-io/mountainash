"""Cross-backend result verification for list/array operations.

Verifies that list expression operations produce identical results across
backends with native array column support. Uses reduced backend set since
pandas, narwhals-pandas, ibis-polars, and ibis-sqlite lack native array types.
"""

from __future__ import annotations

import pytest

import mountainash as ma


LIST_BACKENDS = ["polars", "narwhals-polars", "ibis-duckdb"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListSum:
    def test_sum_basic(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[1, 2, 3], [4, 5], [6, 7, 8, 9]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.sum())
        assert actual == [6, 9, 30]

    def test_sum_with_nulls_in_list(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[1, None, 3], [None, 5], [None]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.sum())
        assert actual == [4, 5, 0] or actual == [4, 5, None]

    def test_sum_empty_list(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[1, 2], [], [3]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.sum())
        assert actual[0] == 3
        assert actual[1] in [0, None]
        assert actual[2] == 3

    def test_sum_single_element(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[5], [10], [15]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.sum())
        assert actual == [5, 10, 15]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListMin:
    def test_min_basic(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[3, 1, 2], [9, 5], [4, 8, 6, 7]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.min())
        assert actual == [1, 5, 4]

    def test_min_with_nulls(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[3, None, 1], [None, 5]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.min())
        assert actual == [1, 5]

    def test_min_single_element(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[42], [7]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.min())
        assert actual == [42, 7]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListMax:
    def test_max_basic(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[3, 1, 2], [9, 5], [4, 8, 6, 7]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.max())
        assert actual == [3, 9, 8]

    def test_max_with_nulls(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[3, None, 1], [None, 5]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.max())
        assert actual == [3, 5]

    def test_max_single_element(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[42], [7]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.max())
        assert actual == [42, 7]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListMean:
    def test_mean_basic(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[2, 4, 6], [10, 20], [1, 2, 3, 4]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.mean())
        assert actual == pytest.approx([4.0, 15.0, 2.5], rel=1e-9)

    def test_mean_with_nulls(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[2, None, 6], [None, 20]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.mean())
        assert actual == pytest.approx([4.0, 20.0], rel=1e-9)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListLen:
    def test_len_basic(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[1, 2, 3], [4, 5], [6, 7, 8, 9]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.len())
        assert actual == [3, 2, 4]

    def test_len_empty(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[], [1], [1, 2]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.len())
        assert actual == [0, 1, 2]

    def test_len_with_nulls_in_list(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[1, None, 3], [None, None]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.len())
        assert actual == [3, 2]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListFirst:
    def test_first_basic(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[10, 20, 30], [40, 50], [60]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.first())
        assert actual == [10, 40, 60]

    def test_first_with_null_first(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[None, 20, 30], [10, None]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.first())
        assert actual == [None, 10]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListLast:
    def test_last_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals list.get() rejects negative index (-1) needed for last()")
        data = {"arr": [[10, 20, 30], [40, 50], [60]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.last())
        assert actual == [30, 50, 60]

    def test_last_with_null_last(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals list.get() rejects negative index (-1) needed for last()")
        data = {"arr": [[10, 20, None], [None, 50]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.last())
        assert actual == [None, 50]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListSort:
    def test_sort_basic(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[3, 1, 2], [9, 5, 7], [4, 8, 6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.sort())
        assert actual == [[1, 2, 3], [5, 7, 9], [4, 6, 8]]

    def test_sort_already_sorted(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[1, 2, 3], [4, 5, 6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.sort())
        assert actual == [[1, 2, 3], [4, 5, 6]]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListReverse:
    def test_reverse_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.reverse() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3], [4, 5], [6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.reverse())
        assert actual == [[3, 2, 1], [5, 4], [6]]

    def test_reverse_empty(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.reverse() not supported on {backend_name}")
        data = {"arr": [[], [1], [1, 2]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.reverse())
        assert actual == [[], [1], [2, 1]]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListUnique:
    def test_unique_basic(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[1, 2, 2, 3, 3, 3], [4, 4, 5]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.unique())
        # Order may vary — sort for comparison
        assert sorted(actual[0]) == [1, 2, 3]
        assert sorted(actual[1]) == [4, 5]

    def test_unique_no_duplicates(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[1, 2, 3], [4, 5, 6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.unique())
        assert sorted(actual[0]) == [1, 2, 3]
        assert sorted(actual[1]) == [4, 5, 6]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListContains:
    def test_contains_present(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals list.contains() fails with expression literal TypeError")
        data = {"arr": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.contains(2))
        assert actual == [True, False, False]

    def test_contains_absent(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals list.contains() fails with expression literal TypeError")
        data = {"arr": [[1, 2, 3], [4, 5, 6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.contains(99))
        assert actual == [False, False]

    def test_contains_in_all(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals list.contains() fails with expression literal TypeError")
        data = {"arr": [[1, 2, 3], [2, 4, 6], [2, 8, 10]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.contains(2))
        assert actual == [True, True, True]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListJoin:
    def test_join_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("list.join() not supported on narwhals")
        data = {"arr": [["a", "b", "c"], ["x", "y"], ["hello"]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.join("-"))
        assert actual == ["a-b-c", "x-y", "hello"]

    def test_join_empty_separator(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("list.join() not supported on narwhals")
        data = {"arr": [["a", "b", "c"], ["x", "y"]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.join(""))
        assert actual == ["abc", "xy"]

    def test_join_single_element(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("list.join() not supported on narwhals")
        data = {"arr": [["only"], ["one"]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.join(","))
        assert actual == ["only", "one"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListSlice:
    def test_slice_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.slice() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3, 4, 5], [10, 20, 30, 40]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.slice(1, length=3))
        assert actual == [[2, 3, 4], [20, 30, 40]]

    def test_slice_from_start(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.slice() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3, 4, 5], [10, 20, 30]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.slice(0, length=2))
        assert actual == [[1, 2], [10, 20]]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListHead:
    def test_head_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.head() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3, 4, 5], [10, 20, 30]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.head(3))
        assert actual == [[1, 2, 3], [10, 20, 30]]

    def test_head_n_larger_than_list(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.head() not supported on {backend_name}")
        data = {"arr": [[1, 2], [10]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.head(5))
        assert actual == [[1, 2], [10]]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListTail:
    def test_tail_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.tail() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3, 4, 5], [10, 20, 30]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.tail(2))
        assert actual == [[4, 5], [20, 30]]

    def test_tail_n_larger_than_list(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.tail() not supported on {backend_name}")
        data = {"arr": [[1, 2], [10]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.tail(5))
        assert actual == [[1, 2], [10]]
