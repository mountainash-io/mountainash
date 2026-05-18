"""Cross-backend tests for expression argument types in non-string operations.

Tests that non-string operations handle argument types consistently.
Category A params (round decimals, names) are now options and only accept literals.
Category B params (log base, datetime offsets, fill_null) accept expressions where the backend supports it.
"""

import pytest
import mountainash as ma

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


# =============================================================================
# Rounding — decimals is now an option (always literal)
# =============================================================================


@pytest.mark.cross_backend
class TestRoundArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_round_literal_decimals(self, backend_name, backend_factory, collect_expr):
        data = {"val": [3.14159, 2.71828]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").round(2)
        actual = collect_expr(df, expr)
        assert actual == [3.14, 2.72], f"[{backend_name}] got {actual}"


# =============================================================================
# Logarithmic — base is an argument (Polars + Ibis accept Expr)
# =============================================================================


@pytest.mark.cross_backend
class TestLogArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_log_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"val": [100.0, 1000.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").log(10.0)
        actual = collect_expr(df, expr)
        assert abs(actual[0] - 2.0) < 0.01, f"[{backend_name}] got {actual}"
        assert abs(actual[1] - 3.0) < 0.01, f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_log_column_reference_base(self, backend_name, backend_factory, collect_expr):
        data = {"val": [100.0, 1000.0], "base": [10.0, 10.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").log(ma.col("base"))
        actual = collect_expr(df, expr)
        assert abs(actual[0] - 2.0) < 0.01, f"[{backend_name}] got {actual}"
        assert abs(actual[1] - 3.0) < 0.01, f"[{backend_name}] got {actual}"
