"""Tests for Relation schema/dtypes/width introspection."""
import polars as pl
import mountainash as ma


class TestRelationSchema:
    def test_schema_bare_relation(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [1.0, 2.0], "c": ["x", "y"]})
        r = ma.relation(df)
        schema = r.schema
        assert "a" in schema
        assert "b" in schema
        assert "c" in schema
        assert len(schema) == 3

    def test_schema_after_select(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [1.0, 2.0], "c": ["x", "y"]})
        r = ma.relation(df).select("a", "b")
        schema = r.schema
        assert list(schema.keys()) == ["a", "b"]

    def test_schema_after_with_columns(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [3, 4]})
        r = ma.relation(df).with_columns(ma.col("a").add(ma.col("b")).alias("c"))
        schema = r.schema
        assert "c" in schema
        assert len(schema) == 3

    def test_schema_after_rename(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [3, 4]})
        r = ma.relation(df).rename({"a": "x"})
        schema = r.schema
        assert "x" in schema
        assert "a" not in schema


class TestRelationDtypes:
    def test_dtypes(self):
        df = pl.LazyFrame({"a": [1, 2], "b": [1.0, 2.0]})
        r = ma.relation(df)
        dtypes = r.dtypes
        assert len(dtypes) == 2


class TestRelationWidth:
    def test_width(self):
        df = pl.LazyFrame({"a": [1], "b": [2], "c": [3]})
        r = ma.relation(df)
        assert r.width == 3

    def test_width_after_select(self):
        df = pl.LazyFrame({"a": [1], "b": [2], "c": [3]})
        r = ma.relation(df).select("a")
        assert r.width == 1


class TestRelationExplain:
    def test_explain_polars_returns_string(self):
        df = pl.LazyFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        r = ma.relation(df).filter(ma.col("a").gt(1)).select("a", "b")
        plan = r.explain()
        assert isinstance(plan, str)
        assert len(plan) > 0

    def test_explain_contains_filter_info(self):
        df = pl.LazyFrame({"a": [1, 2, 3]})
        r = ma.relation(df).filter(ma.col("a").gt(1))
        plan = r.explain()
        assert "FILTER" in plan or "filter" in plan.lower()
