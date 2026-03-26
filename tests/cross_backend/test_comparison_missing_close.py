"""Cross-backend tests for eq_missing, ne_missing, and is_close (Batch 7).

All three are AST-level composition methods — no backend-specific implementation needed.
"""

import pytest
import mountainash_expressions as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestEqMissing:
    def test_eq_missing_equal_values(self, backend_name, backend_factory, select_and_extract):
        data = {"a": [1, 2, 3], "b": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").eq_missing(ma.col("b"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [True, True, True], f"[{backend_name}] got {actual}"

    def test_eq_missing_different_values(self, backend_name, backend_factory, select_and_extract):
        data = {"a": [1, 2, 3], "b": [1, 9, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").eq_missing(ma.col("b"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    def test_eq_missing_both_null(self, backend_name, backend_factory, select_and_extract):
        data = {"a": [1.0, None, 3.0], "b": [1.0, None, 4.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").eq_missing(ma.col("b"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        # None == None should be True (that's the whole point of eq_missing)
        assert actual == [True, True, False], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNeMissing:
    def test_ne_missing_basic(self, backend_name, backend_factory, select_and_extract):
        data = {"a": [1.0, None, 3.0], "b": [1.0, None, 4.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").ne_missing(ma.col("b"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        # None == None should be False for ne_missing
        assert actual == [False, False, True], f"[{backend_name}] got {actual}"


IS_CLOSE_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="Ibis type inference fails on nested abs() expressions")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="Ibis type inference fails on nested abs() expressions")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="Ibis type inference fails on nested abs() expressions")),
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", IS_CLOSE_BACKENDS)
class TestIsClose:
    def test_is_close_exact(self, backend_name, backend_factory, select_and_extract):
        data = {"a": [1.0, 2.0, 3.0], "b": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").is_close(ma.col("b"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [True, True, True], f"[{backend_name}] got {actual}"

    def test_is_close_within_tolerance(self, backend_name, backend_factory, select_and_extract):
        data = {"a": [1.0, 2.0], "b": [1.001, 2.001]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").is_close(ma.col("b"), abs_tol=0.01)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [True, True], f"[{backend_name}] got {actual}"

    def test_is_close_outside_tolerance(self, backend_name, backend_factory, select_and_extract):
        data = {"a": [1.0, 2.0], "b": [1.1, 2.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").is_close(ma.col("b"), abs_tol=0.01, rel_tol=0.0)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [False, False], f"[{backend_name}] got {actual}"
