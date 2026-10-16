"""Cross-backend tests for regex_contains refactor.

Covers:
- Literal regex pattern (Bug 1: regex_contains was routing through literal CONTAINS)
- Column-reference regex pattern (per-row pattern)
- Column-reference literal contains (Bug 2: Polars str.contains with colref)
"""

from __future__ import annotations

from importlib.metadata import version

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
@pytest.mark.parametrize("case_sensitive", [True, False])
def test_regex_pattern_projection(backend_name, backend_factory, shape, case_sensitive):
    """Per-row patterns retain names and payload without hiding native limits."""
    data = {
        "id": list(range(7)),
        "value": ["AU", "NZ", "abc", "", None, "AU", "AU"],
        "pattern": ["^AU$", "^AU$", "^", "^", "^", None, "au"],
    }
    pattern = ma.col("pattern")
    if shape == "computed":
        pattern = pattern.str.lower()
    value = ma.lit("AU") if shape == "literal-receiver" else ma.col("value")
    query = ma.relation(backend_factory.create(data, backend_name)).with_columns(
        ma.when(value.str.regex_contains(pattern, case_sensitive=case_sensitive))
        .then(1).otherwise(-1).alias("score")
    )
    assert query.columns == ["id", "value", "pattern", "score"]
    unsupported = backend_name in {"pandas", "narwhals-pandas", "ibis-polars"}
    error_type = UnsupportedArgumentError if backend_name == "ibis-polars" else TypeError
    if backend_name in {"pandas", "narwhals-pandas"} and (
        version("narwhals") == "2.27.1" and version("pandas") == "3.0.6"
    ):
        error_type = BackendCapabilityError
    with expect_call_failure(
        when=unsupported,
        errors=(error_type,),
        reason="NW-STR-08: pandas dynamic regex is gated on the qualified stack; other native limits remain",
    ):
        result = query.to_polars().sort("id")
        expected = {
            (True, "column"): [1, -1, 1, 1, -1, -1, -1],
            (True, "computed"): [-1, -1, 1, 1, -1, -1, -1],
            (True, "literal-receiver"): [1, 1, 1, 1, 1, -1, -1],
            (False, "column"): [1, -1, 1, 1, -1, -1, 1],
            (False, "computed"): [1, -1, 1, 1, -1, -1, 1],
            (False, "literal-receiver"): [1, 1, 1, 1, 1, -1, 1],
        }[case_sensitive, shape]
        assert result["score"].to_list() == expected
        assert result.select("id", "value", "pattern").to_dict(as_series=False) == data


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", REGEX_BACKENDS)
@pytest.mark.parametrize("shape", ["contains", "literal-expression", "match"])
@pytest.mark.parametrize(
    "pattern,case_sensitive,expected",
    [
        ("au", True, [False, True, False, False, False, False]),
        ("au", False, [True, True, True, False, False, False]),
        ("(?i:au)", True, [True, True, True, False, False, False]),
        ("(?-i:au)", False, [False, True, False, False, False, False]),
    ],
)
def test_regex_case_sensitivity(
    backend_name, backend_factory, shape, pattern, case_sensitive, expected
):
    """Honor the option without breaking literals or explicit inline overrides."""
    data = {"id": list(range(7)), "value": ["AU", "au", "aU", "xauy", "123", "", None]}
    value = ma.col("value")
    if shape == "match":
        predicate = value.str.regex_match(pattern, case_sensitive=case_sensitive)
    else:
        pattern = f"^{pattern}$"
        if shape == "literal-expression":
            pattern = ma.lit(pattern)
        predicate = value.str.regex_contains(pattern, case_sensitive=case_sensitive)
    result = (
        ma.relation(backend_factory.create(data, backend_name))
        .select(ma.col("id"), predicate.alias("match"))
        .to_polars()
        .sort("id")["match"]
        .to_list()
    )
    assert result[:6] == expected
    if backend_name in {"pandas", "narwhals-pandas"}:
        assert result[6] is False or result[6] is None
    else:
        assert result[6] is None


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
@pytest.mark.parametrize("pattern,sensitive", [("^AU$", False), ("(?i)^au$", True)])
def test_native_ibis_regex_literal_preserves_values(
    backend_name, backend_factory, collect_expr, pattern, sensitive,
):
    """Ibis-native literal inspection is backend-specific; generic cases stay above."""
    import ibis

    frame = backend_factory.create({"value": ["AU", "au", "NZ", "", None, "AU"]}, backend_name)
    expression = ma.col("value").str.regex_contains(
        ma.native(ibis.literal(pattern)), case_sensitive=sensitive,
    )
    assert collect_expr(frame, expression) == [True, True, False, False, None, True]
