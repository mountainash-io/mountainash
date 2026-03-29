"""Test that TableBuilder.filter() integrates with mountainash expressions."""
import pytest
import polars as pl

import mountainash as ma
from mountainash.dataframes import table


class TestExpressionIntegration:
    """Verify TableBuilder.filter() accepts BaseExpressionAPI objects."""

    def test_filter_with_gt_expression(self):
        """Filter with ma.col().gt() produces correct results."""
        df = pl.DataFrame({"age": [25, 35, 45], "name": ["alice", "bob", "charlie"]})
        result = table(df).filter(ma.col("age").gt(30)).to_polars()
        assert result.shape[0] == 2
        assert result["name"].to_list() == ["bob", "charlie"]

    def test_filter_with_compound_expression(self):
        """Filter with compound AND expression."""
        df = pl.DataFrame({
            "age": [25, 35, 45, 55],
            "score": [90, 60, 80, 70],
        })
        expr = ma.col("age").gt(30).and_(ma.col("score").ge(70))
        result = table(df).filter(expr).to_polars()
        assert result.shape[0] == 2
        assert result["age"].to_list() == [45, 55]

    def test_filter_with_string_expression(self):
        """Filter with string contains expression."""
        df = pl.DataFrame({"name": ["alice", "bob", "charlie", "david"]})
        result = table(df).filter(ma.col("name").str.contains("a")).to_polars()
        assert result.shape[0] == 3  # alice, charlie, david

    def test_filter_with_native_expression_still_works(self):
        """Native Polars expressions still work (not broken by integration)."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5]})
        result = table(df).filter(pl.col("x") > 3).to_polars()
        assert result.shape[0] == 2

    def test_filter_chain_mixed(self):
        """Chain mountainash and native filters."""
        df = pl.DataFrame({"x": [1, 2, 3, 4, 5], "y": [10, 20, 30, 40, 50]})
        result = (
            table(df)
            .filter(ma.col("x").gt(2))
            .filter(pl.col("y") < 50)
            .to_polars()
        )
        assert result.shape[0] == 2  # x=3,y=30 and x=4,y=40

    def test_top_level_table_import(self):
        """ma.table() is accessible at top level."""
        df = pl.DataFrame({"a": [1]})
        result = ma.table(df).to_polars()
        assert result.shape == (1, 1)

    def test_where_alias_with_expression(self):
        """where() alias also accepts mountainash expressions."""
        df = pl.DataFrame({"x": [1, 2, 3]})
        result = table(df).where(ma.col("x").gt(1)).to_polars()
        assert result.shape[0] == 2
