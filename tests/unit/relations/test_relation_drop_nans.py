"""Tests for Relation.drop_nans()."""
import polars as pl
import mountainash as ma


class TestDropNans:
    def test_drop_nans_removes_nan_rows(self):
        df = pl.LazyFrame({"a": [1.0, float("nan"), 3.0], "b": [4.0, 5.0, 6.0]})
        r = ma.relation(df).drop_nans()
        result = r.to_dicts()
        assert len(result) == 2
        assert result[0]["a"] == 1.0
        assert result[1]["a"] == 3.0

    def test_drop_nans_with_subset(self):
        df = pl.LazyFrame({
            "a": [1.0, float("nan"), 3.0],
            "b": [float("nan"), 5.0, 6.0],
        })
        r = ma.relation(df).drop_nans(subset=["a"])
        result = r.to_dicts()
        assert len(result) == 2

    def test_drop_nans_mixed_types_only_checks_float(self):
        df = pl.LazyFrame({
            "name": ["alice", "bob", "carol"],
            "score": [1.0, float("nan"), 3.0],
            "rank": [1, 2, 3],
        })
        r = ma.relation(df).drop_nans()
        result = r.to_dicts()
        assert len(result) == 2
        assert result[0]["name"] == "alice"
        assert result[1]["name"] == "carol"
