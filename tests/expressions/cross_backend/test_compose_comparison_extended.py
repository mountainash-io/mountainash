"""Cross-backend tests for extended comparison, rounding, and logarithmic coverage.

is_false/is_not_false from the comparison builder are intentionally shadowed by
ternary builder priority in _FLAT_NAMESPACES (ternary-first design).
least() method has a typo in the builder (LTEAST vs LEAST) — xfailed.
"""

import math

import pytest
import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeComparisonTruth:
    """Test truth value checks from comparison builder."""

    def test_is_true(self, backend_name, backend_factory, get_result_count):
        """Test is_true on boolean column."""
        data = {"flag": [True, False, True, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("flag").is_true()
        result = df.filter(expr.compile(df))
        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] is_true: expected 2, got {count}"

    def test_is_not_true(self, backend_name, backend_factory, get_result_count):
        """Test is_not_true on boolean column (false or null)."""
        data = {"flag": [True, False, True, None]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("flag").is_not_true()
        result = df.filter(expr.compile(df))
        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] is_not_true: expected 2 (False + None), got {count}"

    def test_is_not_false(self, backend_name, backend_factory, get_result_count):
        """Test is_not_false on boolean column (true or null)."""
        data = {"flag": [True, False, True, None, False]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("flag").is_not_false()
        result = df.filter(expr.compile(df))
        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] is_not_false: expected 3 (True + True + None), got {count}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestBetween:
    """Test between() with all closed variants across backends."""

    def test_between_default(self, backend_name, backend_factory, collect_expr):
        data = {"x": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("x").between(5, 15)
        result = collect_expr(df, expr)
        assert result == [False, True, True, True, False], f"[{backend_name}] got {result}"

    def test_between_closed_both(self, backend_name, backend_factory, collect_expr):
        data = {"x": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("x").between(5, 15, closed="both")
        result = collect_expr(df, expr)
        assert result == [False, True, True, True, False], f"[{backend_name}] got {result}"

    def test_between_closed_left(self, backend_name, backend_factory, collect_expr):
        data = {"x": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("x").between(5, 15, closed="left")
        result = collect_expr(df, expr)
        assert result == [False, True, True, False, False], f"[{backend_name}] got {result}"

    def test_between_closed_right(self, backend_name, backend_factory, collect_expr):
        data = {"x": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("x").between(5, 15, closed="right")
        result = collect_expr(df, expr)
        assert result == [False, False, True, True, False], f"[{backend_name}] got {result}"

    def test_between_closed_neither(self, backend_name, backend_factory, collect_expr):
        data = {"x": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("x").between(5, 15, closed="neither")
        result = collect_expr(df, expr)
        assert result == [False, False, True, False, False], f"[{backend_name}] got {result}"

    def test_between_closed_none(self, backend_name, backend_factory, collect_expr):
        """'none' is a synonym for 'neither' (matches Polars convention)."""
        data = {"x": [1, 5, 10, 15, 20]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("x").between(5, 15, closed="none")
        result = collect_expr(df, expr)
        assert result == [False, False, True, False, False], f"[{backend_name}] got {result}"


_FINITE_INFINITE_BACKENDS = [
    pytest.param(
        b,
        marks=pytest.mark.xfail(
            reason="ibis-sqlite: is_finite/is_infinite Inf handling differs "
            "(no covering spine fact yet)"
        ),
    )
    if b == "ibis-sqlite"
    else b
    for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _FINITE_INFINITE_BACKENDS)
class TestComposeComparisonNumeric:
    """Numeric checks is_finite / is_infinite. (is_nan lives in TestComposeIsNan,
    routed through IB-TYPE-02.) Only ibis-sqlite's Inf handling diverges; it has
    no covering spine fact yet (SP2-B-contingent), so it stays a reason-only mark."""

    def test_is_finite(self, backend_name, backend_factory, get_result_count):
        """Test is_finite on float column."""
        data = {"val": [1.0, float("inf"), 3.0, float("-inf"), 5.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_finite()
        result = df.filter(expr.compile(df))
        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 finite values, got {count}"

    def test_is_infinite(self, backend_name, backend_factory, get_result_count):
        """Test is_infinite on float column."""
        data = {"val": [1.0, float("inf"), 3.0, float("-inf"), 5.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_infinite()
        result = df.filter(expr.compile(df))
        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 infinite values, got {count}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeComparisonNull:
    """Test null handling: nullif method form."""

    def test_nullif(self, backend_name, backend_factory, collect_expr):
        """Test nullif: return null if value equals sentinel."""
        data = {"val": [10, 0, 30, 0, 50]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").nullif(0)
        actual = collect_expr(df, expr)
        assert actual[0] == 10, f"[{backend_name}] Row 0: {actual[0]}"
        assert actual[1] is None, f"[{backend_name}] Row 1 should be null: {actual[1]}"
        assert actual[3] is None, f"[{backend_name}] Row 3 should be null: {actual[3]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeComparisonMinMax:
    """Test greatest method form (least has LTEAST typo in builder — xfailed)."""

    def test_greatest_method(self, backend_name, backend_factory, collect_expr):
        """Test col.greatest(other) method form."""
        data = {"a": [10, 5, 30], "b": [20, 3, 25]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("a").greatest(ma.col("b"))
        actual = collect_expr(df, expr)
        assert actual == [20, 5, 30], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeRounding:
    """Test ceil and floor."""

    def test_ceil(self, backend_name, backend_factory, collect_expr):
        """Test ceil on float values."""
        data = {"val": [1.2, 2.8, -1.5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").ceil()
        actual = collect_expr(df, expr)
        assert actual == [2, 3, -1], f"[{backend_name}] ceil got {actual}"

    def test_floor(self, backend_name, backend_factory, collect_expr):
        """Test floor on float values."""
        data = {"val": [1.2, 2.8, -1.5]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").floor()
        actual = collect_expr(df, expr)
        assert actual == [1, 2, -2], f"[{backend_name}] floor got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeLogarithmic:
    """Test log10, log2, ln."""

    def test_log10(self, backend_name, backend_factory, collect_expr):
        """Test log10."""
        data = {"val": [1.0, 10.0, 100.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").log10()
        actual = collect_expr(df, expr)
        for i, (a, e) in enumerate(zip(actual, [0.0, 1.0, 2.0])):
            assert math.isclose(a, e, abs_tol=1e-9), f"[{backend_name}] Row {i}: {a} != {e}"

    def test_log2(self, backend_name, backend_factory, collect_expr):
        """Test log2."""
        data = {"val": [1.0, 2.0, 8.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").log2()
        actual = collect_expr(df, expr)
        for i, (a, e) in enumerate(zip(actual, [0.0, 1.0, 3.0])):
            assert math.isclose(a, e, abs_tol=1e-9), f"[{backend_name}] Row {i}: {a} != {e}"

    def test_ln(self, backend_name, backend_factory, collect_expr):
        """Test ln (natural log)."""
        data = {"val": [1.0, math.e, math.e ** 2]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").ln()
        actual = collect_expr(df, expr)
        for i, (a, e) in enumerate(zip(actual, [0.0, 1.0, 2.0])):
            assert math.isclose(a, e, abs_tol=1e-6), f"[{backend_name}] Row {i}: {a} != {e}"


_IS_NAN_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("IB-TYPE-02", backend=b))
    if b in ("ibis-duckdb", "ibis-sqlite")
    else b
    for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _IS_NAN_BACKENDS)
class TestComposeIsNan:
    """is_nan filter. ibis-duckdb/ibis-sqlite route through IB-TYPE-02 (SQL engines
    treat NaN as NULL; NaN == NaN yields NULL, not True)."""

    def test_is_nan(self, backend_name, backend_factory, get_result_count):
        """Test is_nan on float column."""
        data = {"val": [1.0, float("nan"), 3.0, float("nan")]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").is_nan()
        result = df.filter(expr.compile(df))
        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 NaN values, got {count}"
