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
