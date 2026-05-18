"""Cross-backend tests for least() and least_skip_null()."""

import pytest
import mountainash.expressions as ma

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
class TestLeast:
    def test_least_two_columns(self, backend_name, backend_factory, collect_expr):
        """Test least() returns the smaller of two columns."""
        data = {"a": [10, 5, 30], "b": [20, 3, 25]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").least(ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == [10, 3, 25], f"[{backend_name}] got {actual}"

    def test_least_three_columns(self, backend_name, backend_factory, collect_expr):
        """Test least() with three arguments."""
        data = {"a": [10, 50, 30], "b": [20, 3, 25], "c": [15, 10, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").least(ma.col("b"), ma.col("c"))
        actual = collect_expr(df, expr)
        assert actual == [10, 3, 5], f"[{backend_name}] got {actual}"
