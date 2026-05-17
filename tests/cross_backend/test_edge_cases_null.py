"""Cross-backend edge case verification for NULL propagation semantics.

Tests how NULL values propagate through arithmetic, comparison, string,
and coalesce operations. SQL backends follow three-valued logic; Polars
has its own NULL semantics. Differences are expected and documented.
"""

from __future__ import annotations

import pytest

import mountainash as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNullArithmeticPropagation:

    def test_null_plus_integer(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 3], "b": [10, 10, 10]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") + ma.col("b"))
        assert actual[0] == 11
        assert actual[1] is None
        assert actual[2] == 13

    def test_null_multiply(self, backend_name, backend_factory, collect_expr):
        data = {"a": [2, None, 4], "b": [3, 3, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") * ma.col("b"))
        assert actual[0] == 6
        assert actual[1] is None
        assert actual[2] == 12

    def test_null_subtract(self, backend_name, backend_factory, collect_expr):
        data = {"a": [10, None, 30], "b": [1, 1, 1]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") - ma.col("b"))
        assert actual[0] == 9
        assert actual[1] is None
        assert actual[2] == 29

    def test_null_divide(self, backend_name, backend_factory, collect_expr):
        data = {"a": [10.0, None, 30.0], "b": [2.0, 2.0, 2.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") / ma.col("b"))
        assert actual[0] == pytest.approx(5.0)
        assert actual[1] is None
        assert actual[2] == pytest.approx(15.0)


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNullComparisonPropagation:

    def test_null_greater_than(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, None, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").gt(ma.lit(4)))
        assert actual[0] is True
        assert actual[1] in [None, False]
        assert actual[2] is False

    def test_null_equals_value(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, None, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").eq(ma.lit(5)))
        assert actual[0] is True
        assert actual[1] in [None, False]
        assert actual[2] is True

    def test_null_not_equals(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, None, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").ne(ma.lit(5)))
        assert actual[0] is False
        assert actual[1] in [None, True]
        assert actual[2] is True


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNullStringPropagation:

    def test_null_string_concat(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["hello", None, "world"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") + ma.lit("_suffix"))
        assert actual[0] == "hello_suffix"
        assert actual[1] is None
        assert actual[2] == "world_suffix"

    def test_null_string_length(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["hello", None, "ab"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").str.length())
        assert actual[0] == 5
        assert actual[1] is None
        assert actual[2] == 2


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNullCoalesce:

    def test_coalesce_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [None, 2, None], "b": [10, None, 30]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.coalesce(ma.col("a"), ma.col("b")))
        assert actual == [10, 2, 30]

    def test_coalesce_all_null(self, backend_name, backend_factory, collect_expr):
        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB cannot create tables with all-NULL typed columns")
        data = {"a": [None, None, None], "b": [None, None, None]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.coalesce(ma.col("a"), ma.col("b")))
        assert actual == [None, None, None]

    def test_coalesce_with_literal_default(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.coalesce(ma.col("a"), ma.lit(99)))
        assert actual == [1, 99, 3]
