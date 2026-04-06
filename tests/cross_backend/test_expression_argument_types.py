"""Cross-backend tests for expression argument types in string operations.

Tests that string operations handle four argument types consistently:
- RAW_SCALAR: raw Python value ("world")
- EXPRESSION_LITERAL: ma.lit("world")
- COLUMN_REFERENCE: ma.col("pattern")
- COMPLEX_EXPRESSION: ma.col("pattern").str.lower()

Where backends cannot support column references, tests are xfail(strict=True)
so they break when the backend adds support.
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
# Search Operations — contains
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestContainsArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_contains_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "world cup"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains("world")
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_contains_expr_literal(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "world cup"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains(ma.lit("world"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis-polars compiler requires literal for contains")),
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_contains_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "world cup"], "pattern": ["world", "baz", "cup"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains(ma.col("pattern"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis-polars compiler requires literal for contains")),
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_contains_complex_expression(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "world cup"], "pattern": ["WORLD", "BAZ", "CUP"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.contains(ma.col("pattern").str.lower())
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"


# =============================================================================
# Search Operations — starts_with
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestStartsWithArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_starts_with_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "help me"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.starts_with("hel")
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_starts_with_expr_literal(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "help me"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.starts_with(ma.lit("hel"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis-polars compiler requires literal for starts_with")),
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_starts_with_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "help me"], "prefix": ["hel", "baz", "hel"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.starts_with(ma.col("prefix"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"


# =============================================================================
# Search Operations — ends_with
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestEndsWithArgTypes:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_ends_with_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "my world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.ends_with("world")
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis-polars compiler requires literal for ends_with")),
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals requires literal")),
    ])
    def test_ends_with_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "foo bar", "my world"], "suffix": ["world", "baz", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.ends_with(ma.col("suffix"))
        actual = collect_expr(df, expr)
        assert actual == [True, False, True], f"[{backend_name}] got {actual}"


# =============================================================================
# Search Operations — strpos
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestStrposArgTypes:

    @pytest.mark.parametrize("backend_name", [
        "polars",
        "ibis-polars",
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals strpos not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals strpos not implemented")),
    ])
    def test_strpos_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello", "world"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.strpos("lo")
        actual = collect_expr(df, expr)
        assert actual[0] > 0, f"[{backend_name}] 'hello' should contain 'lo'"
        assert actual[1] == 0, f"[{backend_name}] 'world' should not contain 'lo'"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis-polars compiler requires literal for strpos")),
        "ibis-duckdb",
        "ibis-sqlite",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals strpos not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals strpos not implemented")),
    ])
    def test_strpos_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello", "world"], "sub": ["lo", "xyz"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.strpos(ma.col("sub"))
        actual = collect_expr(df, expr)
        assert actual[0] > 0, f"[{backend_name}] 'hello' should contain 'lo'"
        assert actual[1] == 0, f"[{backend_name}] 'world' should not contain 'xyz'"


# =============================================================================
# Search Operations — count_substring
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.string
class TestCountSubstringArgTypes:

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals count_substring not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals count_substring not implemented")),
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
        pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
        pytest.param("ibis-sqlite", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
    ])
    def test_count_substring_raw_scalar(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["abcabc", "xyz"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring("abc")
        actual = collect_expr(df, expr)
        assert actual == [2, 0], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", [
        "polars",
        pytest.param("pandas", marks=pytest.mark.xfail(
            strict=True, reason="narwhals count_substring not implemented")),
        pytest.param("narwhals", marks=pytest.mark.xfail(
            strict=True, reason="narwhals count_substring not implemented")),
        pytest.param("ibis-polars", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
        pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
        pytest.param("ibis-sqlite", marks=pytest.mark.xfail(
            strict=True, reason="ibis count_substring not implemented")),
    ])
    def test_count_substring_column_reference(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["abcabc", "xyz"], "sub": ["abc", "xyz"]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("text").str.count_substring(ma.col("sub"))
        actual = collect_expr(df, expr)
        assert actual == [2, 1], f"[{backend_name}] got {actual}"
