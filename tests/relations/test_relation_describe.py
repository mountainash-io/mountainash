"""Tests for Relation.describe()."""
import polars as pl
import mountainash as ma


class TestDescribe:
    def test_describe_returns_dataframe(self):
        df = pl.LazyFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        r = ma.relation(df)
        result = r.describe()
        assert isinstance(result, pl.DataFrame)

    def test_describe_has_statistic_column(self):
        df = pl.LazyFrame({"a": [1, 2, 3]})
        r = ma.relation(df)
        result = r.describe()
        assert "statistic" in result.columns

    def test_describe_has_expected_statistics(self):
        df = pl.LazyFrame({"a": [1, 2, 3]})
        r = ma.relation(df)
        result = r.describe()
        stats = result["statistic"].to_list()
        assert "count" in stats
        assert "mean" in stats
        assert "min" in stats
        assert "max" in stats

    def test_describe_multiple_columns(self):
        df = pl.LazyFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        r = ma.relation(df)
        result = r.describe()
        assert "a" in result.columns
        assert "b" in result.columns
