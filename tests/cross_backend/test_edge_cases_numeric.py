"""Cross-backend edge case verification for numeric semantics.

Tests how backends handle division by zero, integer division semantics,
float precision, rounding modes, modulo sign, overflow, and NaN treatment.
"""

from __future__ import annotations

import math

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
class TestDivisionByZero:

    def test_int_divide_by_zero(self, backend_name, backend_factory, collect_expr):
        data = {"a": [10, 20, 30], "b": [2, 0, 5]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") / ma.col("b"))
        assert actual[0] == pytest.approx(5.0)
        # Division by zero: Inf (Polars/pandas), NULL (SQL), or NaN
        assert actual[1] is None or (
            isinstance(actual[1], float)
            and (math.isinf(actual[1]) or math.isnan(actual[1]))
        )
        assert actual[2] == pytest.approx(6.0)

    def test_float_divide_by_zero(self, backend_name, backend_factory, collect_expr):
        data = {"a": [10.0, 20.0], "b": [0.0, 5.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") / ma.col("b"))
        assert actual[0] is None or (
            isinstance(actual[0], float) and math.isinf(actual[0])
        )
        assert actual[1] == pytest.approx(4.0)

    def test_zero_divide_by_zero(self, backend_name, backend_factory, collect_expr):
        data = {"a": [0.0], "b": [0.0]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a") / ma.col("b"))
        # 0/0: NaN (Polars/pandas), NULL (SQL)
        assert actual[0] is None or (
            isinstance(actual[0], float) and math.isnan(actual[0])
        )


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestIntegerDivision:

    def test_positive_floor_div(self, backend_name, backend_factory, collect_expr):
        data = {"a": [7, 10, 15], "b": [2, 3, 4]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").floordiv(ma.col("b")))
        assert actual == [3, 3, 3]

    def test_negative_floor_div(self, backend_name, backend_factory, collect_expr):
        data = {"a": [-7, -10], "b": [2, 3]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("a").floordiv(ma.col("b")))
        # Python/Polars: floor division → [-4, -4]
        # SQL (truncate toward zero): [-3, -3]
        assert actual[0] in [-4, -3]
        assert actual[1] in [-4, -3]
