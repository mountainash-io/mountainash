"""Cross-backend tests for extended string operations coverage.

Tests string methods that have working function key enums and backend
implementations.
"""

import pytest
import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence

_NW_TRIM = [
    pytest.param(b, marks=xfail_divergence("NW-STR-15", backend=b)) for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _NW_TRIM)
class TestComposeStringTrimExtended:
    """Test ltrim and rtrim (trim already covered in test_compose_string.py)."""

    def test_ltrim(self, backend_name, backend_factory, collect_expr):
        """Test ltrim removes leading spaces."""
        data = {"text": ["  hello  ", "  world  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.ltrim()
        actual = collect_expr(df, expr)
        assert actual == ["hello  ", "world  "], f"[{backend_name}] ltrim got {actual}"

    def test_rtrim(self, backend_name, backend_factory, collect_expr):
        """Test rtrim removes trailing spaces."""
        data = {"text": ["  hello  ", "  world  "]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.rtrim()
        actual = collect_expr(df, expr)
        assert actual == ["  hello", "  world"], f"[{backend_name}] rtrim got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeStringRegexExtended:
    """Test regex methods: regexp_replace, regex_contains, regex_match, slice."""

    def test_regexp_replace(self, backend_name, backend_factory, collect_expr):
        """Test regexp_replace: replace regex matches."""
        data = {"text": ["hello 123 world 456", "no digits here"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.regexp_replace(r"\d+", "NUM")
        actual = collect_expr(df, expr)
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

    def test_slice_alias(self, backend_name, backend_factory, collect_expr):
        """Test slice() as substring alias."""
        data = {"text": ["abcdef", "xyz123"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.slice(1, 3)
        actual = collect_expr(df, expr)
        assert len(actual[0]) == 3, f"[{backend_name}] Expected 3-char slice, got {actual}"

    def test_regex_replace_alias(self, backend_name, backend_factory, collect_expr):
        """Test regex_replace convenience alias (delegates to regexp_replace)."""
        data = {"text": ["a1b2c3", "no-digits"]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("text").str.regex_replace(r"\d", "X")
        actual = collect_expr(df, expr)
        assert actual[0] == "aXbXcX", f"[{backend_name}] got {actual[0]}"
        assert actual[1] == "no-digits", f"[{backend_name}] got {actual[1]}"


# A dynamic (column-valued) pattern on regexp_replace: raw `polars`
# (and `polars-lazy`) already gates this cleanly via a pre-existing
# LITERAL_ONLY fact (PL-STR-02, expressions/backends/capabilities/polars.py)
# and every Narwhals variant already gates it too, so ibis-duckdb/
# ibis-sqlite are the ONLY backends where a dynamic pattern genuinely honors
# (verified empirically). ibis-polars is the sole gap this item closes —
# excluded here and asserted cleanly gated instead; see
# test_string.py::TestDynamicPatternIbisPolarsGate.
_REGEXP_REPLACE_DYNAMIC_HONORING = ["ibis-duckdb", "ibis-sqlite"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _REGEXP_REPLACE_DYNAMIC_HONORING)
def test_regexp_replace_dynamic_operand(backend_name, backend_factory, collect_expr):
    """Pattern varies per row (proving per-row evaluation, not a fixed
    value baked in at build time)."""
    data = {"text": ["hello 123", "foo bar"], "pattern": [r"\d+", r"bar"]}
    df = backend_factory.create(data, backend_name)
    expr = ma.col("text").str.regexp_replace(ma.col("pattern"), "NUM")
    assert collect_expr(df, expr) == ["hello NUM", "foo NUM"], f"[{backend_name}]"
