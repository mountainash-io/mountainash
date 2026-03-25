"""Cross-backend tests for extended string operations coverage.

Tests string methods that have working function key enums and backend implementations.
Many string builder methods (swapcase, capitalize, initcap, lpad, rpad, center, left,
right, strpos, count_substring, bit_length, octet_length, concat, repeat, reverse,
replace_slice, concat_ws, string_split, regexp_string_split) reference function key
enums that don't exist yet — these are aspirational and excluded from coverage targets.
"""

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
class TestComposeStringTrimExtended:
    """Test ltrim and rtrim (trim already covered in test_compose_string.py)."""

    def test_ltrim(self, backend_name, backend_factory, select_and_extract):
        """Test ltrim removes leading spaces."""
        if backend_name in ("pandas", "narwhals"):
            pytest.xfail(f"{backend_name}: ltrim strips both sides instead of left only.")
        data = {"text": ["  hello  ", "  world  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.ltrim()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["hello  ", "world  "], f"[{backend_name}] ltrim got {actual}"

    def test_rtrim(self, backend_name, backend_factory, select_and_extract):
        """Test rtrim removes trailing spaces."""
        if backend_name in ("pandas", "narwhals"):
            pytest.xfail(f"{backend_name}: rtrim strips both sides instead of right only.")
        data = {"text": ["  hello  ", "  world  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.rtrim()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == ["  hello", "  world"], f"[{backend_name}] rtrim got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeStringRegexExtended:
    """Test regex methods: regexp_replace, regex_contains, regex_match, slice."""

    def test_regexp_replace(self, backend_name, backend_factory, select_and_extract):
        """Test regexp_replace: replace regex matches."""
        data = {"text": ["hello 123 world 456", "no digits here"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.regexp_replace(r"\d+", "NUM")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] == "hello NUM world NUM", f"[{backend_name}] got {actual[0]}"
        assert actual[1] == "no digits here", f"[{backend_name}] got {actual[1]}"

    def test_regex_contains(self, backend_name, backend_factory, get_result_count):
        """Test regex_contains convenience alias."""
        data = {"email": ["user@test.com", "bad-email", "admin@site.org"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("email").str.regex_contains(r"@")
        result = df.filter(expr.compile(df))
        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2, got {count}"

    def test_regex_match(self, backend_name, backend_factory, get_result_count):
        """Test regex_match: anchored full-string match."""
        data = {"code": ["ABC123", "abc123", "ABC", "123ABC"]}
        df = backend_factory.create(data, backend_name)

        # Match strings that are all uppercase letters followed by digits
        expr = ma.col("code").str.regex_match(r"[A-Z]+\d+")
        result = df.filter(expr.compile(df))
        count = get_result_count(result, backend_name)
        # "ABC123" matches, "abc123" no (lowercase), "ABC" no (no digits), "123ABC" no (digits first)
        assert count == 1, f"[{backend_name}] Expected 1, got {count}"

    def test_slice_alias(self, backend_name, backend_factory, select_and_extract):
        """Test slice() as substring alias."""
        data = {"text": ["abcdef", "xyz123"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.slice(1, 3)
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert len(actual[0]) == 3, f"[{backend_name}] Expected 3-char slice, got {actual}"

    def test_regex_replace_alias(self, backend_name, backend_factory, select_and_extract):
        """Test regex_replace convenience alias (delegates to regexp_replace)."""
        data = {"text": ["a1b2c3", "no-digits"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.regex_replace(r"\d", "X")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] == "aXbXcX", f"[{backend_name}] got {actual[0]}"
        assert actual[1] == "no-digits", f"[{backend_name}] got {actual[1]}"
