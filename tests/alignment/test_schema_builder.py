"""Tests for SchemaBuilder — deferred schema API."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma


@pytest.fixture
def sample_df():
    return pl.DataFrame({
        "age": ["30", "25", "35"],
        "full_name": ["Alice", "Bob", "Charlie"],
        "score": [1.5, None, 3.0],
    })


class TestSchemaBuilderDefinition:
    """ma.schema() creates a deferred SchemaBuilder."""

    def test_schema_returns_schema_builder(self):
        s = ma.schema({"age": {"cast": "integer"}})
        assert hasattr(s, "apply")
        assert hasattr(s, "columns")

    def test_schema_columns_property(self):
        s = ma.schema({
            "age": {"cast": "integer"},
            "name": {"cast": "string"},
        })
        assert s.columns == ["age", "name"]

    def test_schema_transforms_property(self):
        s = ma.schema({
            "age": {"cast": "integer"},
            "name": {"rename": "full_name"},
        })
        transforms = s.transforms
        assert "age" in transforms
        assert "name" in transforms


class TestSchemaBuilderApply:
    """SchemaBuilder.apply() transforms a DataFrame."""

    def test_apply_cast_integer(self, sample_df):
        s = ma.schema({"age": {"cast": "integer"}})
        result = s.apply(sample_df)
        assert isinstance(result, pl.DataFrame)
        assert result["age"].dtype == pl.Int64

    def test_apply_rename(self, sample_df):
        s = ma.schema({"name": {"rename": "full_name"}})
        result = s.apply(sample_df)
        assert "name" in result.columns

    def test_apply_null_fill(self, sample_df):
        s = ma.schema({"score": {"null_fill": 0.0}})
        result = s.apply(sample_df)
        assert result["score"].null_count() == 0
        assert result["score"].to_list() == [1.5, 0.0, 3.0]

    def test_apply_multi_transform(self, sample_df):
        s = ma.schema({
            "age": {"cast": "integer"},
            "score": {"null_fill": 0.0},
        })
        result = s.apply(sample_df)
        assert result["age"].dtype == pl.Int64
        assert result["score"].null_count() == 0

    def test_apply_strict_missing_column_raises(self, sample_df):
        s = ma.schema({"nonexistent": {"cast": "integer"}})
        with pytest.raises(Exception):
            s.apply(sample_df, strict=True)

    def test_apply_lenient_missing_column_skips(self, sample_df):
        s = ma.schema({"nonexistent": {"cast": "integer"}})
        result = s.apply(sample_df)
        # Should not raise, just skip the missing column
        assert result.shape == sample_df.shape
