"""Verify t_is_in/t_is_not_in raise BareExpressionCollectionError at build time for column collections."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.expressions.membership.errors import BareExpressionCollectionError


class TestTernaryIsInExprSupport:
    """Build-time errors for expression-arg t_is_in/t_is_not_in."""

    def test_t_is_in_col_arg_raises_enriched_or_native_error(self):
        with pytest.raises(BareExpressionCollectionError):
            ma.t_col("value").is_in(ma.col("lookup"))

    def test_t_is_not_in_col_arg_raises_enriched_or_native_error(self):
        with pytest.raises(BareExpressionCollectionError):
            ma.t_col("value").is_not_in(ma.col("lookup"))

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
