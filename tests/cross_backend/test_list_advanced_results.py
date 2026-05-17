"""Cross-backend result verification for advanced list operations."""

from __future__ import annotations

import pytest

import mountainash as ma

LIST_BACKENDS = ["polars", "narwhals-polars", "ibis-duckdb"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListGet:
    def test_get_first(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[10, 20, 30], [40, 50], [60]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.get(0))
        assert actual == [10, 40, 60]

    def test_get_last_negative(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals list.get() rejects negative index (-1) [NW-LIST-04]")
        data = {"arr": [[10, 20, 30], [40, 50], [60]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.get(-1))
        assert actual == [30, 50, 60]

    def test_get_middle(self, backend_name, backend_factory, collect_expr):
        data = {"arr": [[10, 20, 30], [40, 50, 60]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.get(1))
        assert actual == [20, 50]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListGatherEvery:
    def test_gather_every_2(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.gather_every() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3, 4, 5, 6], [10, 20, 30, 40]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.gather_every(2))
        assert actual == [[1, 3, 5], [10, 30]]

    def test_gather_every_3(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.gather_every() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3, 4, 5, 6, 7, 8, 9]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.gather_every(3))
        assert actual == [[1, 4, 7]]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListArgMin:
    def test_arg_min_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.arg_min() not supported on {backend_name}")
        data = {"arr": [[30, 10, 20], [5, 15, 3]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.arg_min())
        assert actual == [1, 2]

    def test_arg_min_first_element(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.arg_min() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3], [0, 10, 20]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.arg_min())
        assert actual == [0, 0]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListArgMax:
    def test_arg_max_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.arg_max() not supported on {backend_name}")
        data = {"arr": [[30, 10, 20], [5, 15, 3]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.arg_max())
        assert actual == [0, 1]

    def test_arg_max_last_element(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.arg_max() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3], [10, 20, 30]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.arg_max())
        assert actual == [2, 2]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListAll:
    def test_all_true(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals does not support list.all()")
        data = {"arr": [[True, True, True], [True, False], [False, False]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.all())
        assert actual == [True, False, False]

    def test_all_single(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals does not support list.all()")
        data = {"arr": [[True], [False]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.all())
        assert actual == [True, False]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListAny:
    def test_any_mixed(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals does not support list.any()")
        data = {"arr": [[True, False, True], [False, False], [True, True]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.any())
        assert actual == [True, False, True]

    def test_any_single(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("Narwhals does not support list.any()")
        data = {"arr": [[True], [False]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.any())
        assert actual == [True, False]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListNUnique:
    def test_n_unique_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.n_unique() not supported on {backend_name}")
        data = {"arr": [[1, 2, 2, 3, 3, 3], [4, 4], [1, 2, 3, 4, 5]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.n_unique())
        assert actual == [3, 1, 5]

    def test_n_unique_all_same(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.n_unique() not supported on {backend_name}")
        data = {"arr": [[7, 7, 7], [1]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.n_unique())
        assert actual == [1, 1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListCountMatches:
    def test_count_matches_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.count_matches() not supported on {backend_name}")
        data = {"arr": [[1, 2, 2, 3, 2], [4, 4, 4], [1, 2, 3]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.count_matches(2))
        assert actual == [3, 0, 1]

    def test_count_matches_no_match(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.count_matches() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3], [4, 5, 6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.count_matches(99))
        assert actual == [0, 0]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListDropNulls:
    def test_drop_nulls_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.drop_nulls() not supported on {backend_name}")
        data = {"arr": [[1, None, 3], [None, None], [4, 5]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.drop_nulls())
        assert actual == [[1, 3], [], [4, 5]]

    def test_drop_nulls_no_nulls(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.drop_nulls() not supported on {backend_name}")
        data = {"arr": [[1, 2, 3], [4, 5]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.drop_nulls())
        assert actual == [[1, 2, 3], [4, 5]]
