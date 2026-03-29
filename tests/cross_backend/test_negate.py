"""Cross-backend tests for negate() and __neg__ operator."""

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
class TestNegate:
    def test_negate_method(self, backend_name, backend_factory, select_and_extract):
        """Test negate() method on numeric column."""
        data = {"val": [10, -5, 0, 3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").negate()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [-10, 5, 0, -3], f"[{backend_name}] got {actual}"

    def test_neg_operator(self, backend_name, backend_factory, select_and_extract):
        """Test Python -expr operator (calls __neg__ -> negate())."""
        data = {"val": [10, -5, 0, 3]}
        df = backend_factory.create(data, backend_name)

        expr = -ma.col("val")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [-10, 5, 0, -3], f"[{backend_name}] got {actual}"

    def test_negate_in_expression(self, backend_name, backend_factory, select_and_extract):
        """Test negate composed with arithmetic."""
        data = {"val": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        expr = (-ma.col("val")).add(100)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [90, 80, 70], f"[{backend_name}] got {actual}"
