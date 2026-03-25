"""Cross-backend tests for arithmetic essentials: abs, sqrt, sign, exp."""

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
class TestAbs:
    def test_abs_positive(self, backend_name, backend_factory, select_and_extract):
        """abs() on positive values returns same values."""
        data = {"val": [1, 2, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [1, 2, 3], f"[{backend_name}] got {actual}"

    def test_abs_negative(self, backend_name, backend_factory, select_and_extract):
        """abs() on negative values returns positive values."""
        data = {"val": [-10, -5, 0, 3]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [10, 5, 0, 3], f"[{backend_name}] got {actual}"

    def test_abs_floats(self, backend_name, backend_factory, select_and_extract):
        """abs() on floats."""
        data = {"val": [-1.5, 2.5, -3.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").abs()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        for a, e in zip(actual, [1.5, 2.5, 3.0]):
            assert math.isclose(a, e, abs_tol=1e-9), f"[{backend_name}] {a} != {e}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSqrt:
    def test_sqrt(self, backend_name, backend_factory, select_and_extract):
        """sqrt() on positive values."""
        if backend_name in ("narwhals", "pandas"):
            pytest.xfail(f"{backend_name}: sqrt() not supported by Narwhals backend.")
        data = {"val": [1.0, 4.0, 9.0, 16.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").sqrt()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        for a, e in zip(actual, [1.0, 2.0, 3.0, 4.0]):
            assert math.isclose(a, e, abs_tol=1e-9), f"[{backend_name}] {a} != {e}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSign:
    def test_sign(self, backend_name, backend_factory, select_and_extract):
        """sign() returns -1, 0, or 1."""
        if backend_name in ("narwhals", "pandas"):
            pytest.xfail(f"{backend_name}: sign() not supported by Narwhals backend.")
        data = {"val": [-10, 0, 5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").sign()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [-1, 0, 1], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestExp:
    def test_exp(self, backend_name, backend_factory, select_and_extract):
        """exp() computes e^x."""
        if backend_name in ("narwhals", "pandas"):
            pytest.xfail(f"{backend_name}: exp() not supported by Narwhals backend.")
        data = {"val": [0.0, 1.0, 2.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").exp()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        for a, e in zip(actual, [1.0, math.e, math.e**2]):
            assert math.isclose(a, e, abs_tol=1e-6), f"[{backend_name}] {a} != {e}"
