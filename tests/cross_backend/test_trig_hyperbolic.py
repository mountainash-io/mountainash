"""Cross-backend tests for trigonometric, hyperbolic, and angular conversion operations."""

import math

import pytest
import mountainash.expressions as ma

# Polars + Ibis have native trig support (including SQLite via ibis)
TRIG_BACKENDS = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals lacks trig methods")),
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

# Only Polars has native hyperbolic support
HYPERBOLIC_BACKENDS = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals lacks hyperbolic methods")),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis lacks hyperbolic methods")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="ibis lacks hyperbolic methods")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="sqlite lacks hyperbolic functions")),
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
