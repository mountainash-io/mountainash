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


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListSetUnion:
    def test_set_union_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("list.set_union() not supported on narwhals")
        data = {"a": [[1, 2, 3], [4, 5]], "b": [[2, 3, 4], [5, 6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").list.set_union(ma.col("b")))
        assert sorted(actual[0]) == [1, 2, 3, 4]
        assert sorted(actual[1]) == [4, 5, 6]

    def test_set_union_no_overlap(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("list.set_union() not supported on narwhals")
        data = {"a": [[1, 2]], "b": [[3, 4]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").list.set_union(ma.col("b")))
        assert sorted(actual[0]) == [1, 2, 3, 4]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListSetIntersection:
    def test_set_intersection_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("list.set_intersection() not supported on narwhals")
        data = {"a": [[1, 2, 3], [4, 5]], "b": [[2, 3, 4], [5, 6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").list.set_intersection(ma.col("b")))
        assert sorted(actual[0]) == [2, 3]
        assert sorted(actual[1]) == [5]

    def test_set_intersection_no_overlap(self, backend_name, backend_factory, collect_expr):
        if backend_name == "narwhals-polars":
            pytest.xfail("list.set_intersection() not supported on narwhals")
        data = {"a": [[1, 2]], "b": [[3, 4]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").list.set_intersection(ma.col("b")))
        assert actual == [[]]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListSetDifference:
    def test_set_difference_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.set_difference() not supported on {backend_name}")
        data = {"a": [[1, 2, 3], [4, 5, 6]], "b": [[2, 3], [6]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").list.set_difference(ma.col("b")))
        assert sorted(actual[0]) == [1]
        assert sorted(actual[1]) == [4, 5]

    def test_set_difference_complete(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.set_difference() not supported on {backend_name}")
        data = {"a": [[1, 2, 3]], "b": [[1, 2, 3]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").list.set_difference(ma.col("b")))
        assert actual == [[]]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListMedian:
    def test_median_odd(self, backend_name, backend_factory, collect_expr):
        if backend_name == "ibis-duckdb":
            pytest.xfail("list.median() not supported on ibis")
        data = {"arr": [[1, 3, 5], [2, 4, 6, 8, 10]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.median())
        assert actual == pytest.approx([3.0, 6.0])

    def test_median_even(self, backend_name, backend_factory, collect_expr):
        if backend_name == "ibis-duckdb":
            pytest.xfail("list.median() not supported on ibis")
        data = {"arr": [[1, 3, 5, 7], [2, 4]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.median())
        assert actual == pytest.approx([4.0, 3.0])


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListStd:
    def test_std_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.std() not supported on {backend_name}")
        data = {"arr": [[2, 4, 4, 4, 5, 5, 7, 9]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.std())
        assert actual[0] is not None
        assert actual == pytest.approx([2.0], rel=0.15)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", LIST_BACKENDS)
class TestListVar:
    def test_var_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("narwhals-polars", "ibis-duckdb"):
            pytest.xfail(f"list.var() not supported on {backend_name}")
        data = {"arr": [[2, 4, 4, 4, 5, 5, 7, 9]]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("arr").list.var())
        assert actual[0] is not None
        assert actual == pytest.approx([4.0], rel=0.2)
