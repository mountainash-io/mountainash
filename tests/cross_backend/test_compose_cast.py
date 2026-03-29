"""Cross-backend tests for cast fluent composition."""

import math

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
class TestComposeCast:
    """Test cast operations composed with other builders."""

    def test_cast_float_then_divide(self, backend_name, backend_factory, select_and_extract):
        """Cast to float then divide: .cast(float).divide(total)."""
        data = {"value": [10, 20, 30], "total": [100.0, 100.0, 100.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("value").cast(float).divide(ma.col("total"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        for i, (a, e) in enumerate(zip(actual, [0.1, 0.2, 0.3])):
            assert math.isclose(a, e, rel_tol=1e-9), f"[{backend_name}] Row {i}: {a} != {e}"

    def test_cast_to_string_then_contains(self, backend_name, backend_factory, get_result_count):
        """Cast int to string then search: .cast(str).str.contains('5')."""
        data = {"count": [15, 25, 30, 50, 55]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("count").cast(str).str.contains("5")
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # "15" has 5, "25" has 5, "30" no, "50" has 5, "55" has 5
        assert count == 4, f"[{backend_name}] Expected 4, got {count}"

    def test_cast_then_compare(self, backend_name, backend_factory, get_result_count):
        """Cast float to int then compare: .cast(int).gt(70)."""
        if backend_name == "ibis-duckdb":
            pytest.xfail("DuckDB uses banker's rounding for float-to-int cast, not truncation.")
        data = {"score": [70.5, 69.9, 71.0, 50.3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("score").cast(int).gt(70)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # 70.5 -> 70 (truncated), not > 70
        # 69.9 -> 69, not > 70
        # 71.0 -> 71, > 70 yes
        # 50.3 -> 50, no
        assert count == 1, f"[{backend_name}] Expected 1 (71), got {count}"

    def test_fill_null_cast_multiply(self, backend_name, backend_factory, select_and_extract):
        """Chain: fill_null -> cast -> multiply."""
        data = {"price": [10, None, 30], "rate": [1.1, 1.2, 1.3]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("price").fill_null(0).cast(float).multiply(ma.col("rate"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert math.isclose(actual[0], 11.0, rel_tol=1e-9), f"[{backend_name}] Row 0: {actual[0]}"
        assert math.isclose(actual[1], 0.0, abs_tol=1e-9), f"[{backend_name}] Row 1: {actual[1]}"
        assert math.isclose(actual[2], 39.0, rel_tol=1e-9), f"[{backend_name}] Row 2: {actual[2]}"
