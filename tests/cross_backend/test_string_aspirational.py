"""Cross-backend tests for aspirational string operations (Batch 4).

Tests for newly wired string operations. Backend support varies significantly.
"""

import pytest
import mountainash_expressions as ma

POLARS_IBIS = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals fallback")),
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_ONLY = [
    "polars",
    pytest.param("pandas", marks=pytest.mark.xfail(reason="pandas backend limited")),
    pytest.param("narwhals", marks=pytest.mark.xfail(reason="narwhals fallback")),
    pytest.param("ibis-polars", marks=pytest.mark.xfail(reason="ibis backend issues")),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(reason="ibis backend issues")),
    pytest.param("ibis-sqlite", marks=pytest.mark.xfail(reason="sqlite fallback")),
]

POLARS_NARWHALS_IBIS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


# =============================================================================
# Case conversion
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestCapitalize:
    def test_capitalize(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello world", "foo bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.capitalize()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["Hello world", "Foo bar"], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY)
class TestTitle:
    def test_title(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello world", "foo bar"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.title()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["Hello World", "Foo Bar"], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_ONLY)
class TestSwapcase:
    def test_swapcase(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["Hello", "WORLD"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.swapcase()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["hELLO", "world"], f"[{backend_name}] got {actual}"


# =============================================================================
# Padding (lpad/rpad now use _extract_literal_value correctly)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestPadding:
    def test_lpad(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.lpad(5, " ")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["   hi", "  hey"], f"[{backend_name}] got {actual}"

    def test_rpad(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hi", "hey"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.rpad(5, " ")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["hi   ", "hey  "], f"[{backend_name}] got {actual}"


# =============================================================================
# Extraction (left/right now use _extract_literal_value correctly)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_NARWHALS_IBIS)
class TestExtraction:
    def test_left(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.left(3)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["hel", "wor"], f"[{backend_name}] got {actual}"

    def test_right(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.right(3)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["llo", "rld"], f"[{backend_name}] got {actual}"


# =============================================================================
# Length variants (work across Polars + Ibis)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestLengthVariants:
    def test_bit_length(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["a", "ab"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.bit_length()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [8, 16], f"[{backend_name}] got {actual}"

    def test_octet_length(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["a", "ab"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.octet_length()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [1, 2], f"[{backend_name}] got {actual}"


# =============================================================================
# Manipulation
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestRepeat:
    def test_repeat(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["ab", "cd"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.repeat(3)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["ababab", "cdcdcd"], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestReverse:
    def test_reverse(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.reverse()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["olleh", "dlrow"], f"[{backend_name}] got {actual}"


# =============================================================================
# Search (strpos works across Polars + Ibis)
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS)
class TestSearch:
    def test_strpos(self, backend_name, backend_factory, select_and_extract):
        data = {"val": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("val").str.strpos("lo")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        # strpos is 1-indexed; 0 means not found
        assert actual[0] > 0, f"[{backend_name}] 'hello' should contain 'lo', got {actual[0]}"
        assert actual[1] == 0, f"[{backend_name}] 'world' should not contain 'lo', got {actual[1]}"
