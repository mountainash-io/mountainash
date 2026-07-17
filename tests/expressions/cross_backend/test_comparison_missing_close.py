"""Cross-backend tests for eq_missing, ne_missing, and is_close (Batch 7).

All three are AST-level composition methods — no backend-specific implementation needed.
"""

import pytest
import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestEqMissing:
    def test_eq_missing_equal_values(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3], "b": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").eq_missing(ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == [True, True, True], f"[{backend_name}] got {actual}"

    def test_eq_missing_different_values(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1, 2, 3], "b": [1, 9, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").eq_missing(ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    def test_eq_missing_both_null(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, None, 3.0], "b": [1.0, None, 4.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").eq_missing(ma.col("b"))
        actual = collect_expr(df, expr)
        # None == None should be True (that's the whole point of eq_missing)
        assert actual == [True, True, False], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNeMissing:
    def test_ne_missing_basic(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, None, 3.0], "b": [1.0, None, 4.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").ne_missing(ma.col("b"))
        actual = collect_expr(df, expr)
        # None == None should be False for ne_missing
        assert actual == [False, False, True], f"[{backend_name}] got {actual}"


# is_close builds literal-left arithmetic internally — MULTIPLY(lit rel_tol, abs(other))
# and ADD(lit abs_tol, rel_part) — so the ibis crash here was the literal-first
# arithmetic bug (IB-TYPE-01 / Ibis #11742), NOT "nested abs()" as the old xfail
# reason claimed. Resolved by _lift_deferred (item 226b); the ibis params now run.
IS_CLOSE_BACKENDS = [
    "polars",
    "polars-lazy",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", IS_CLOSE_BACKENDS)
class TestIsClose:
    def test_is_close_exact(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, 2.0, 3.0], "b": [1.0, 2.0, 3.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").is_close(ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == [True, True, True], f"[{backend_name}] got {actual}"

    def test_is_close_within_tolerance(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, 2.0], "b": [1.001, 2.001]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").is_close(ma.col("b"), abs_tol=0.01)
        actual = collect_expr(df, expr)
        assert actual == [True, True], f"[{backend_name}] got {actual}"

    def test_is_close_outside_tolerance(self, backend_name, backend_factory, collect_expr):
        data = {"a": [1.0, 2.0], "b": [1.1, 2.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("a").is_close(ma.col("b"), abs_tol=0.01, rel_tol=0.0)
        actual = collect_expr(df, expr)
        assert actual == [False, False], f"[{backend_name}] got {actual}"
