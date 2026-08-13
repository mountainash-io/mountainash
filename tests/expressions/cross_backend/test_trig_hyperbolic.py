"""Cross-backend tests for trigonometric, hyperbolic, and angular conversion operations."""

import math

import pytest
import mountainash.expressions as ma
from fixtures.capability_gating import xfail_divergence

# Polars + Ibis have native trig support (including SQLite via ibis); pandas and
# narwhals lack trig/angular functions (NW-MATH-10).
TRIG_BACKENDS = [
    "polars",
    "polars-lazy",
    pytest.param("pandas", marks=xfail_divergence("NW-MATH-10", backend="pandas")),
    pytest.param("narwhals-polars", marks=xfail_divergence("NW-MATH-10", backend="narwhals-polars")),
    pytest.param("narwhals-pandas", marks=xfail_divergence("NW-MATH-10", backend="narwhals-pandas")),
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

# Only Polars has native hyperbolic support: pandas/narwhals lack it (NW-MATH-10),
# ibis-polars/ibis-duckdb lack it (IB-MATH-06), ibis-sqlite lacks it (IB-MATH-02).
HYPERBOLIC_BACKENDS = [
    "polars",
    "polars-lazy",
    pytest.param("pandas", marks=xfail_divergence("NW-MATH-10", backend="pandas")),
    pytest.param("narwhals-polars", marks=xfail_divergence("NW-MATH-10", backend="narwhals-polars")),
    pytest.param("narwhals-pandas", marks=xfail_divergence("NW-MATH-10", backend="narwhals-pandas")),
    pytest.param("ibis-polars", marks=xfail_divergence("IB-MATH-06", backend="ibis-polars")),
    pytest.param("ibis-duckdb", marks=xfail_divergence("IB-MATH-06", backend="ibis-duckdb")),
    pytest.param("ibis-sqlite", marks=xfail_divergence("IB-MATH-02", backend="ibis-sqlite")),
]


def approx(values, abs_tol=1e-6):
    return [pytest.approx(v, abs=abs_tol) for v in values]


# =============================================================================
# Trigonometric
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TRIG_BACKENDS)
class TestTrig:
    def test_sin(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, math.pi / 2, math.pi]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").sin()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, 1.0, 0.0]), f"[{backend_name}] got {actual}"

    def test_cos(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, math.pi / 2, math.pi]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").cos()
        actual = collect_expr(df, expr)
        assert actual == approx([1.0, 0.0, -1.0]), f"[{backend_name}] got {actual}"

    def test_tan(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, math.pi / 4]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").tan()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, 1.0]), f"[{backend_name}] got {actual}"


# =============================================================================
# Inverse Trigonometric
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TRIG_BACKENDS)
class TestInverseTrig:
    def test_asin(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").asin()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.pi / 2]), f"[{backend_name}] got {actual}"

    def test_acos(self, backend_name, backend_factory, collect_expr):
        data = {"val": [1.0, 0.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").acos()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.pi / 2]), f"[{backend_name}] got {actual}"

    def test_atan(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").atan()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.pi / 4]), f"[{backend_name}] got {actual}"

    def test_atan2(self, backend_name, backend_factory, collect_expr):
        data = {"y": [1.0, 0.0], "x": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("y").atan2(ma.col("x"))
        actual = collect_expr(df, expr)
        assert actual == approx([math.pi / 2, 0.0]), f"[{backend_name}] got {actual}"


# =============================================================================
# Angular Conversion
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TRIG_BACKENDS)
class TestAngularConversion:
    def test_radians(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, 90.0, 180.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").radians()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.pi / 2, math.pi]), f"[{backend_name}] got {actual}"

    def test_degrees(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, math.pi / 2, math.pi]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").degrees()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, 90.0, 180.0]), f"[{backend_name}] got {actual}"


# =============================================================================
# Hyperbolic
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", HYPERBOLIC_BACKENDS)
class TestHyperbolic:
    def test_sinh(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").sinh()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.sinh(1.0)]), f"[{backend_name}] got {actual}"

    def test_cosh(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").cosh()
        actual = collect_expr(df, expr)
        assert actual == approx([1.0, math.cosh(1.0)]), f"[{backend_name}] got {actual}"

    def test_tanh(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").tanh()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.tanh(1.0)]), f"[{backend_name}] got {actual}"


# =============================================================================
# Inverse Hyperbolic
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", HYPERBOLIC_BACKENDS)
class TestInverseHyperbolic:
    def test_asinh(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, 1.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").asinh()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.asinh(1.0)]), f"[{backend_name}] got {actual}"

    def test_acosh(self, backend_name, backend_factory, collect_expr):
        data = {"val": [1.0, 2.0]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").acosh()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.acosh(2.0)]), f"[{backend_name}] got {actual}"

    def test_atanh(self, backend_name, backend_factory, collect_expr):
        data = {"val": [0.0, 0.5]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").atanh()
        actual = collect_expr(df, expr)
        assert actual == approx([0.0, math.atanh(0.5)]), f"[{backend_name}] got {actual}"
