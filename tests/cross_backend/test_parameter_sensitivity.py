"""Cross-backend parameter sensitivity tests.

Verifies that operation parameters actually reach the backend and affect output.
Each test uses discriminating data: if the parameter were silently dropped or
defaulted, the assertion would fail.

See: g.development-practices/testing-philosophy.md § Discriminating Test Data
"""

import math
import pytest
from datetime import datetime

import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_IBIS = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals limited")),
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

TEMPORAL_BACKENDS = [
    "polars",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


# =============================================================================
# Rounding — round(decimals) must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRoundParameterSensitivity:
    """round(decimals) must produce different results for different decimals."""

    def test_round_value_correctness(self, backend_name, backend_factory, select_and_extract):
        """round(2) produces correct 2-decimal values."""
        data = {"val": [1.555, 2.345, 3.789]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").round(2)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # 1.555 → 1.56 (or 1.55 with banker's rounding — both differ from round(0)=2)
        # Key: none of these should be whole numbers
        for val in actual:
            assert val != int(val), (
                f"[{backend_name}] round(2) produced whole number {val} — "
                f"parameter may be silently ignored (defaulting to round(0))"
            )

    def test_round_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """round(1) and round(2) must produce different results."""
        data = {"val": [1.555, 2.345, 3.789]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda d: ma.col("val").round(d),
            1, 2,
            backend_name,
        )


# =============================================================================
# Logarithmic — log(base) must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLogParameterSensitivity:
    """log(base) must use the base parameter."""

    def test_log_base10_value_correctness(self, backend_name, backend_factory, select_and_extract):
        """log(10) of powers of 10 produces exact integers."""
        data = {"val": [10.0, 100.0, 1000.0]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").log(10)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        for got, expected in zip(actual, [1.0, 2.0, 3.0]):
            assert math.isclose(got, expected, abs_tol=1e-9), (
                f"[{backend_name}] log(10) of {10 ** int(expected)} = {got}, expected {expected}"
            )

    def test_log_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """log(2) and log(10) must produce different results."""
        data = {"val": [100.0, 1000.0]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda b: ma.col("val").log(b),
            2, 10,
            backend_name,
        )


# =============================================================================
# String trim — trim(chars) must use the characters parameter
# =============================================================================


TRIM_CUSTOM_CHARS_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis trim ignores custom chars")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="ibis trim ignores custom chars")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="ibis trim ignores custom chars")),
]

# ltrim/rtrim custom chars only works on Polars; narwhals/pandas/ibis silently ignore the parameter
LTRIM_RTRIM_CUSTOM_CHARS_BACKENDS = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas ltrim/rtrim ignores custom chars")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals ltrim/rtrim ignores custom chars")),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis trim ignores custom chars")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="ibis trim ignores custom chars")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="ibis trim ignores custom chars")),
]


@pytest.mark.cross_backend
class TestTrimParameterSensitivity:
    """trim/ltrim/rtrim with custom characters must actually strip those chars."""

    @pytest.mark.parametrize("backend_name", TRIM_CUSTOM_CHARS_BACKENDS)
    def test_trim_custom_chars_value(self, backend_name, backend_factory, select_and_extract):
        """trim('x') strips x chars, not whitespace."""
        data = {"val": ["xxhelloxx", "xworldx"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.trim("x")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", LTRIM_RTRIM_CUSTOM_CHARS_BACKENDS)
    def test_ltrim_custom_chars_value(self, backend_name, backend_factory, select_and_extract):
        """ltrim('.') strips leading dots."""
        data = {"val": ["..hello", "...world"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.ltrim(".")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", LTRIM_RTRIM_CUSTOM_CHARS_BACKENDS)
    def test_rtrim_custom_chars_value(self, backend_name, backend_factory, select_and_extract):
        """rtrim('#') strips trailing hashes."""
        data = {"val": ["hello##", "world#"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.rtrim("#")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        assert actual == ["hello", "world"], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", TRIM_CUSTOM_CHARS_BACKENDS)
    def test_trim_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """trim('x') and trim('.') must produce different results."""
        data = {"val": ["x.hello.x"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda c: ma.col("val").str.trim(c),
            "x", ".",
            backend_name,
        )


# =============================================================================
# String padding — lpad/rpad width must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestPadParameterSensitivity:
    """lpad/rpad width parameter must reach the backend."""

    def test_lpad_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """lpad(5) and lpad(8) must produce different results."""
        data = {"val": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda w: ma.col("val").str.lpad(w, " "),
            5, 8,
            backend_name,
        )

    def test_rpad_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """rpad(5) and rpad(8) must produce different results."""
        data = {"val": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda w: ma.col("val").str.rpad(w, " "),
            5, 8,
            backend_name,
        )


# =============================================================================
# String extraction — left/right count must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLeftRightParameterSensitivity:
    """left(n)/right(n) count parameter must reach the backend."""

    def test_left_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """left(2) and left(4) must produce different results."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda n: ma.col("val").str.left(n),
            2, 4,
            backend_name,
        )

    def test_right_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """right(2) and right(4) must produce different results."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda n: ma.col("val").str.right(n),
            2, 4,
            backend_name,
        )


# =============================================================================
# String repeat — repeat(n) count must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestRepeatParameterSensitivity:
    """repeat(n) count parameter must reach the backend."""

    def test_repeat_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """repeat(2) and repeat(3) must produce different results."""
        data = {"val": ["ab", "cd"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda n: ma.col("val").str.repeat(n),
            2, 3,
            backend_name,
        )


# =============================================================================
# Substring — start and length must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSubstringParameterSensitivity:
    """substring(start, length) parameters must reach the backend."""

    def test_substring_start_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """substring(0, 3) and substring(2, 3) must produce different results."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda s: ma.col("val").str.slice(s, 3),
            0, 2,
            backend_name,
        )

    def test_substring_length_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """substring(0, 2) and substring(0, 4) must produce different results."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda l: ma.col("val").str.slice(0, l),
            2, 4,
            backend_name,
        )


# =============================================================================
# Datetime arithmetic — duration must affect output
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDatetimeParameterSensitivity:
    """add_days/add_hours duration must reach the backend."""

    def test_add_days_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """add_days(1) and add_days(5) must produce different results."""
        data = {"ts": [datetime(2024, 1, 15, 10, 0, 0)]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda d: ma.col("ts").dt.add_days(d),
            1, 5,
            backend_name,
        )

    def test_add_hours_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """add_hours(1) and add_hours(12) must produce different results."""
        data = {"ts": [datetime(2024, 1, 15, 10, 0, 0)]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda h: ma.col("ts").dt.add_hours(h),
            1, 12,
            backend_name,
        )


# =============================================================================
# Center — width and char must affect output (Polars only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals limited")),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis no center")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="ibis no center")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="ibis no center")),
])
class TestCenterParameterSensitivity:
    """center(width, char) parameters must reach the backend."""

    def test_center_value_correctness(self, backend_name, backend_factory, select_and_extract):
        """center(7, '*') pads both sides."""
        data = {"val": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.center(7, "*")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # "hi" centered in 7 with '*' → "**hi***" or "***hi**" (implementation may vary)
        assert all(len(s) == 7 for s in actual), f"[{backend_name}] widths: {[len(s) for s in actual]}"
        assert all("*" in s for s in actual), f"[{backend_name}] no padding chars: {actual}"

    def test_center_width_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """center(5) and center(9) must produce different results."""
        data = {"val": ["hi"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda w: ma.col("val").str.center(w, "*"),
            5, 9,
            backend_name,
        )


# =============================================================================
# Replace slice — start, length, replacement must affect output (Polars only)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals limited")),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis no replace_slice")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="ibis no replace_slice")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="ibis no replace_slice")),
])
class TestReplaceSliceParameterSensitivity:
    """replace_slice(start, length, replacement) parameters must reach backend."""

    def test_replace_slice_value_correctness(self, backend_name, backend_factory, select_and_extract):
        """replace_slice(1, 3, 'XY') replaces characters 1-3."""
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("val").str.replace_slice(1, 3, "XY")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)

        # Key assertion: the result is NOT "hello" (parameter was used)
        assert actual[0] != "hello", f"[{backend_name}] replace_slice had no effect: {actual}"
        assert "XY" in actual[0], f"[{backend_name}] replacement not found in: {actual}"

    def test_replace_slice_length_sensitivity(self, backend_name, backend_factory, assert_parameter_sensitivity):
        """replace_slice with length 1 and length 3 must differ."""
        data = {"val": ["hello"]}
        df = backend_factory.create(data, backend_name)

        assert_parameter_sensitivity(
            df,
            lambda l: ma.col("val").str.replace_slice(1, l, "X"),
            1, 3,
            backend_name,
        )
