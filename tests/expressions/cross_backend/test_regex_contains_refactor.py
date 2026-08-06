"""Cross-backend tests for regex_contains refactor.

Covers:
- Literal regex pattern (Bug 1: regex_contains was routing through literal CONTAINS)
- Column-reference regex pattern (per-row pattern)
- Column-reference literal contains (Bug 2: Polars str.contains with colref)
"""
from __future__ import annotations

import pytest

import mountainash.expressions as ma


# Custom list: narwhals-pandas excluded — str.contains rejects columnar pattern (pre-existing xfail)
ALL_BACKENDS = [
    "polars",
    "polars-lazy",
    "pandas",
    "narwhals-polars",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

from fixtures.capability_gating import xfail_divergence

_COL = [
    pytest.param(b, marks=xfail_divergence("MA-STR-01", backend=b)) for b in ALL_BACKENDS
]

@pytest.mark.cross_backend
class TestRegexContainsRefactor:

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_regex_contains_literal_pattern(self, backend_name, backend_factory, collect_expr):
        """regex_contains with a literal regex string must match via regex, not literal."""
        data = {
            "s": ["PREFIX_a", "PREFIX_b", "other", "PRE_no_suffix", None],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("s").str.regex_contains("^PREFIX_.*")
        actual = collect_expr(df, expr)
        # Non-null rows: must agree across all backends.
        assert actual[:4] == [True, True, False, False], (
            f"[{backend_name}] Expected first 4 == [True, True, False, False], got {actual}"
        )
        # Null-input row: pandas (via narwhals) returns False instead of
        # propagating null — known divergence, not in scope for this fix.
        if backend_name == "pandas":
            assert actual[4] is False or actual[4] is None, (
                f"[{backend_name}] Expected False/None at idx 4, got {actual[4]!r}"
            )
        else:
            assert actual[4] is None, (
                f"[{backend_name}] Expected None at idx 4, got {actual[4]!r}"
            )

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_regex_contains_column_pattern_rejected(self, backend_name, backend_factory, collect_expr):
        """regex_contains rejects column-reference patterns at build time.

        Per arguments-vs-options.md, the regex pattern is a universally-literal
        parameter. Dynamic per-row patterns are not supported on any backend;
        users who need them should reach for Relation.compile() and drop into
        the native backend. This test replaces the former
        ``test_regex_contains_column_pattern`` which asserted the opposite.
        """
        with pytest.raises(TypeError, match="literal str"):
            ma.col("s").str.regex_contains(ma.col("pat"))

    @pytest.mark.parametrize("backend_name", _COL)
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
