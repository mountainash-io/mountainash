"""Cross-backend tests for regex_contains refactor.

Covers:
- Literal regex pattern (Bug 1: regex_contains was routing through literal CONTAINS)
- Column-reference regex pattern (per-row pattern)
- Column-reference literal contains (Bug 2: Polars str.contains with colref)
"""
from __future__ import annotations

import pytest

import mountainash.expressions as ma


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
class TestRegexContainsRefactor:

    def test_regex_contains_literal_pattern(self, backend_name, backend_factory, collect_expr):
        """regex_contains with a literal regex string must match via regex, not literal."""
        data = {
            "s": ["PREFIX_a", "PREFIX_b", "other", "PRE_no_suffix", None],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("s").str.regex_contains("^PREFIX_.*")
        actual = collect_expr(df, expr)
        assert actual == [True, True, False, False, None], (
            f"[{backend_name}] Expected [True, True, False, False, None], got {actual}"
        )

    def test_regex_contains_column_pattern(self, backend_name, backend_factory, collect_expr):
        """regex_contains with a per-row pattern column."""
        data = {
            "s": ["abc123", "xyz", "hello world", "foo"],
            "pat": [r"\d+", r"^x", r"\s", r"^bar"],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("s").str.regex_contains(ma.col("pat"))
        actual = collect_expr(df, expr)
        assert actual == [True, True, True, False], (
            f"[{backend_name}] Expected [True, True, True, False], got {actual}"
        )

    def test_contains_column_pattern(self, backend_name, backend_factory, collect_expr):
        """Literal contains with a per-row pattern column (Bug 2)."""
        data = {
            "s": ["apple pie", "banana split", "cherry", "date"],
            "needle": ["pie", "split", "XX", "dat"],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("s").str.contains(ma.col("needle"))
        actual = collect_expr(df, expr)
        assert actual == [True, True, False, True], (
            f"[{backend_name}] Expected [True, True, False, True], got {actual}"
        )
