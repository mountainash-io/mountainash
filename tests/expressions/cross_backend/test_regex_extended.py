"""Cross-backend tests for extended regex operations (extract_all, strpos, count).

Tests for: regexp_match_substring_all, regexp_strpos, regexp_count_substring.

Backend support: these three operations are Polars-only and raise
BackendCapabilityError on Narwhals and Ibis backends (strict=True).
"""
from __future__ import annotations

import pytest

import mountainash as ma


# ---------------------------------------------------------------------------
# Backend lists
# ---------------------------------------------------------------------------

REGEX_POLARS_ONLY = [
    "polars",
    pytest.param("narwhals-polars", marks=pytest.mark.xfail(
        strict=True,
        reason="Narwhals does not support regexp_match_substring_all/regexp_strpos/regexp_count_substring — raises BackendCapabilityError",
    )),
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
        strict=True,
        reason="Ibis does not support regexp_match_substring_all/regexp_strpos/regexp_count_substring — raises BackendCapabilityError",
    )),
]


# =============================================================================
# regexp_match_substring_all
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", REGEX_POLARS_ONLY)
class TestRegexpMatchSubstringAll:
    """regexp_match_substring_all extracts all regex matches as a list (Polars-only)."""

    def test_basic_extract_all(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["abc 123 def 456", "no digits", "7 ate 9"]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("text").str.regexp_match_substring_all(r"\d+"))
        assert result == [["123", "456"], [], ["7", "9"]], (
            f"[{backend_name}] got {result}"
        )


# =============================================================================
# regexp_strpos
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", REGEX_POLARS_ONLY)
class TestRegexpStrpos:
    """regexp_strpos returns 1-indexed position of first regex match (Polars-only)."""

    def test_basic_position(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["hello world", "no match", "abc123"]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("text").str.regexp_strpos(r"\d+"))
        assert result == [0, 0, 4], f"[{backend_name}] got {result}"


# =============================================================================
# regexp_count_substring
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", REGEX_POLARS_ONLY)
class TestRegexpCountSubstring:
    """regexp_count_substring counts non-overlapping regex matches (Polars-only)."""

    def test_basic_count(self, backend_name, backend_factory, collect_expr):
        data = {"text": ["aaa bbb aaa", "no match", "aaa"]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("text").str.regexp_count_substring(r"aaa"))
        assert result == [2, 0, 1], f"[{backend_name}] got {result}"
