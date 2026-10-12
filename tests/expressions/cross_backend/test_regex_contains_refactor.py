"""Cross-backend tests for regex_contains refactor.

Covers:
- Literal regex pattern (Bug 1: regex_contains was routing through literal CONTAINS)
- Column-reference regex pattern (per-row pattern)
- Column-reference literal contains (Bug 2: Polars str.contains with colref)
"""

from __future__ import annotations

import pytest

import mountainash as ma
from ibis.common.exceptions import UnsupportedArgumentError
from mountainash.core.types import BackendCapabilityError
from fixtures.call_expectations import expect_call_failure
from fixtures.backend_registry import ALL_BACKENDS as REGEX_BACKENDS


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
            assert actual[4] is None, f"[{backend_name}] Expected None at idx 4, got {actual[4]!r}"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_contains_column_pattern(self, backend_name, backend_factory, collect_expr):
        """Literal contains with a per-row pattern column (Bug 2)."""
        data = {
            "s": ["apple pie", "banana split", "cherry", "date"],
            "needle": ["pie", "split", "XX", "dat"],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("s").str.contains(ma.col("needle"))
        with expect_call_failure(
            when=backend_name == 'pandas' or backend_name == 'ibis-polars',
            reason=('Columnar literal contains raises on pandas and ibis-polars.' if backend_name == 'pandas' else 'Columnar literal contains raises on pandas and ibis-polars.'),
            errors=((BackendCapabilityError,) if backend_name == 'pandas' else (UnsupportedArgumentError,)),
        ):
            actual = collect_expr(df, expr)
            assert actual == [True, True, False, True], f"[{backend_name}] Expected [True, True, False, True], got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", REGEX_BACKENDS)
@pytest.mark.parametrize("shape", ["column", "computed", "literal-receiver"])
def test_regex_pattern_projection(backend_name, backend_factory, shape):
    """Per-row patterns retain names and payload without hiding native limits."""
    data = {
        "id": list(range(7)),
        "value": ["AU", "NZ", "abc", "", None, "AU", "AU"],
        "pattern": ["^AU$", "^AU$", "^", "^", "^", None, "au"],
    }
    pattern = ma.col("pattern")
    if shape == "computed":
        pattern = pattern.str.upper()
    value = ma.lit("AU") if shape == "literal-receiver" else ma.col("value")
    query = ma.relation(backend_factory.create(data, backend_name)).with_columns(
        ma.when(value.str.regex_contains(pattern)).then(1).otherwise(-1).alias("score")
    )
    assert query.columns == ["id", "value", "pattern", "score"]
    unsupported = backend_name in {"pandas", "narwhals-pandas", "ibis-polars"}
    error_type = UnsupportedArgumentError if backend_name == "ibis-polars" else TypeError
    with expect_call_failure(
        when=unsupported,
        errors=(error_type,),
        reason="Native regex predicate rejects a dynamic pattern on this route",
    ):
        result = query.to_polars().sort("id")
        expected = {
            "column": [1, -1, 1, 1, -1, -1, -1],
            "computed": [1, -1, 1, 1, -1, -1, 1],
            "literal-receiver": [1, 1, 1, 1, 1, -1, -1],
        }[shape]
        assert result["score"].to_list() == expected
        assert result.select("id", "value", "pattern").to_dict(as_series=False) == data
