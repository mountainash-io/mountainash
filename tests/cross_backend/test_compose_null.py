"""Cross-backend tests for null handling fluent composition."""

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
class TestComposeNull:
    """Test null handling composed with other operations."""

    def test_fill_null_then_arithmetic(self, backend_name, backend_factory, collect_expr):
        """Fill nulls then add: fill_null(0) + tax."""
        data = {"price": [100, None, 300], "tax": [10, 20, 30]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("price").fill_null(0) + ma.col("tax")
        actual = collect_expr(df, expr)

        assert actual == [110, 20, 330], f"[{backend_name}] Expected [110, 20, 330], got {actual}"

    def test_fill_null_multiply_then_compare(self, backend_name, backend_factory, get_result_count):
        """Chain: fill_null -> multiply -> gt."""
        data = {"value": [60, None, 40, None, 80]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").fill_null(ma.lit(0)).multiply(2).gt(100)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 60*2=120 > 100 yes, 0*2=0 no, 40*2=80 no, 0*2=0 no, 80*2=160 yes
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"

    def test_is_null_or_negative(self, backend_name, backend_factory, get_result_count):
        """Null check in boolean chain: is_null OR value < 0."""
        data = {"a": [10, None, -5, 20, None], "b": [1, 2, 3, 4, 5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").is_null().or_(ma.col("a").lt(0))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 1: null -> yes, Row 2: -5 < 0 -> yes, Row 4: null -> yes
        assert count == 3, f"[{backend_name}] Expected 3, got {count}"

    def test_cascading_fill_null(self, backend_name, backend_factory, collect_expr):
        """Cascading fill: fill_null(col_b).fill_null(0)."""
        data = {"a": [1, None, None], "b": [10, None, 30]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").fill_null(ma.col("b")).fill_null(0)
        actual = collect_expr(df, expr)

        # Row 0: a=1 -> 1
        # Row 1: a=None, b=None -> fill with b=None, then fill with 0 -> 0
        # Row 2: a=None, b=30 -> fill with b=30 -> 30
        assert actual == [1, 0, 30], f"[{backend_name}] Expected [1, 0, 30], got {actual}"
