"""Verify t_is_in/t_is_not_in raise enriched errors for expression collections on narwhals.

On narwhals-polars, collection.list.contains(element) constructs a lazy
expression without error — the failure defers to materialization as a
NarwhalsError (ValueError subclass). The _call_with_expr_support wrapper
is in place to catch construction-time errors on backends that reject
immediately (e.g. future narwhals-pandas support). This test verifies
both paths: the expression-arg path produces a recognisable error, and
the literal-collection path continues to work.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError


def _make_nw_polars_df():
    import polars as pl
    import narwhals as nw
    data = {"value": [1, 2, 3], "lookup": [[1, 4], [2, 5], [3, 6]]}
    return nw.from_native(pl.DataFrame(data), eager_only=True)


class TestTernaryIsInExprSupport:
    """Enriched errors for expression-arg t_is_in on narwhals."""

    def test_t_is_in_col_arg_raises_enriched_or_native_error(self):
        df = _make_nw_polars_df()
        expr = ma.t_col("value").is_in(ma.col("lookup"))
        compiled = expr.compile(df)
        with pytest.raises((BackendCapabilityError, ValueError)):
            df.select(compiled).to_native()

    def test_t_is_not_in_col_arg_raises_enriched_or_native_error(self):
        df = _make_nw_polars_df()
        expr = ma.t_col("value").is_not_in(ma.col("lookup"))
        compiled = expr.compile(df)
        with pytest.raises((BackendCapabilityError, ValueError)):
            df.select(compiled).to_native()

    def test_t_is_in_literal_list_works(self):
        """Regression: literal list argument should work unchanged."""
        import polars as pl
        import narwhals as nw
        data = {"value": [1, 2, 3]}
        df = nw.from_native(pl.DataFrame(data), eager_only=True)
        expr = ma.t_col("value").is_in([1, 2])
        compiled = expr.compile(df)
        result = df.select(compiled).to_native()
        assert len(result) == 3

    def test_t_is_not_in_literal_list_works(self):
        """Regression: literal list argument should work unchanged."""
        import polars as pl
        import narwhals as nw
        data = {"value": [1, 2, 3]}
        df = nw.from_native(pl.DataFrame(data), eager_only=True)
        expr = ma.t_col("value").is_not_in([1, 2])
        compiled = expr.compile(df)
        result = df.select(compiled).to_native()
        assert len(result) == 3
