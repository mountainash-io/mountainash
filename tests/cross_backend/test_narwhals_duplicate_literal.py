"""Cross-backend regression pin for narwhals duplicate 'literal' column names.

Tracks mountainash-expressions#77. narwhals' pandas path materialises
``nw.min_horizontal`` / ``nw.max_horizontal`` arguments as intermediate
columns all named ``literal``, then hits ``check_column_names_are_unique``
before the outer aliases resolve — raising ``DuplicateError``.

The fix (applied in the narwhals ternary backend) replaces
``min_horizontal`` / ``max_horizontal`` with equivalent ``when/then``
expressions that narwhals-pandas handles correctly.

**Test A** exercises the full Relation API path (the path users hit).
**Test B** verifies the raw narwhals ``min_horizontal`` bug still exists
upstream, so we know our workaround is still needed.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations import relation

STRING_SENTINELS = {"?", "<UNKNOWN>"}
NUMERIC_SENTINELS = {-999, -999.0}

ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestDuplicateLiteralRelation:
    """Test A: Full Relation API path — should pass on all backends now."""

    def test_batched_ternary_expressions_in_with_columns(
        self, backend_name, backend_factory
    ):
        """Two sentinel-aware ternary expressions batched in one with_columns.

        Pattern mirrors DimensionCompiler output: EXACT (t_eq) + RANGE
        (t_le / t_ge / t_and) compiled against a DataFrame with context
        columns added via ma.lit().alias().
        """
        data = {
            "region": ["AU", "?"],
            "amount_min": [0, -999],
            "amount_max": [100, -999],
        }
        df = backend_factory.create(data, backend_name)

        rel = relation(df)
        rel = rel.with_columns(
            ma.lit("AU").alias("__ctx_region"),
            ma.lit(50).alias("__ctx_amount"),
        )

        # EXACT dimension: t_col(rule).t_eq(t_col(ctx))
        expr_exact = ma.t_col("region", unknown=STRING_SENTINELS).t_eq(
            ma.t_col("__ctx_region", unknown=STRING_SENTINELS)
        )

        # RANGE dimension: t_col(min).t_le(t_col(ctx)).t_and(t_col(max).t_ge(t_col(ctx)))
        ctx_col = ma.t_col("__ctx_amount", unknown=NUMERIC_SENTINELS)
        min_col = ma.t_col("amount_min", unknown=NUMERIC_SENTINELS)
        max_col = ma.t_col("amount_max", unknown=NUMERIC_SENTINELS)
        expr_range = min_col.t_le(ctx_col).t_and(max_col.t_ge(ctx_col))

        rel = rel.with_columns(
            expr_exact.name.alias("__t_region"),
            expr_range.name.alias("__t_amount"),
        )

        result = rel.to_dict()
        assert result["__t_region"] == [1, 0], (
            f"[{backend_name}] __t_region: expected [1, 0], got {result['__t_region']}"
        )
        assert result["__t_amount"] == [1, 0], (
            f"[{backend_name}] __t_amount: expected [1, 0], got {result['__t_amount']}"
        )


@pytest.mark.cross_backend
class TestMinHorizontalUpstreamBug:
    """Test B: Verify the upstream narwhals bug still exists.

    When narwhals fixes ``min_horizontal`` intermediate naming on pandas,
    this xfail flips to xpass and we can revert ``t_and``/``t_or`` to use
    ``min_horizontal``/``max_horizontal`` again for clarity.
    """

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "narwhals-pandas: nw.min_horizontal materialises arguments as "
            "intermediate columns all named 'literal' — "
            "mountainash-io/mountainash-expressions#77"
        ),
    )
    def test_min_horizontal_duplicate_literal_on_narwhals_pandas(self):
        """nw.min_horizontal(nw.lit(1), nw.lit(2)) fails on pandas."""
        import narwhals as nw
        import pandas as pd

        df = pd.DataFrame({"a": [1, 2]})
        nw_df = nw.from_native(df)

        expr = nw.min_horizontal(nw.lit(1), nw.lit(2))
        nw_df.with_columns(expr.alias("result"))
