"""Cross-backend result verification for comparison and arithmetic extensions."""

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
class TestIsBetween:
    def test_is_between_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(5, 15))
        assert actual == [False, True, True, True, False]

    def test_is_between_boundary(self, backend_name, backend_factory, collect_expr):
        data = {"a": [5, 15]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(5, 15))
        assert actual == [True, True]

    def test_is_between_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 10]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_between(0, 20))
        assert actual[0] is True
        assert actual[1] in [None, False]
        assert actual[2] is True


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestIsIn:
    def test_is_in_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([2, 4]))
        assert actual == [False, True, False, True, False]

    def test_is_in_with_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, None, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([1, 3]))
        assert actual[0] is True
        assert actual[1] in [None, False]
        assert actual[2] is True

    def test_is_in_no_match(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in([99, 100]))
        assert actual == [False, False, False]

    def test_is_in_strings(self, backend_name, backend_factory, collect_expr):
        data = {"a": ["apple", "banana", "cherry"]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").is_in(["banana", "cherry"]))
        assert actual == [False, True, True]
