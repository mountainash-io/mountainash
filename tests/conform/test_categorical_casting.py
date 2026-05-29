"""Tests for categories/categoriesOrdered in conform pipeline."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestCategoricalCasting:
    """Conform pipeline: categories and categoriesOrdered."""

    def test_simple_array_categories_unordered(self):
        """Simple array categories without ordered flag -> pl.Categorical."""
        df = pl.DataFrame({"color": ["red", "blue", "red"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="color",
                    type=UniversalType.STRING,
                    categories=["red", "blue", "green"],
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["color"].to_list() == ["red", "blue", "red"]
        assert result["color"].dtype == pl.Categorical

    def test_simple_array_categories_ordered(self):
        """Ordered categories -> pl.Enum with defined order."""
        df = pl.DataFrame({"size": ["S", "M", "L"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="size",
                    type=UniversalType.STRING,
                    categories=["S", "M", "L", "XL"],
                    categories_ordered=True,
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["size"].to_list() == ["S", "M", "L"]
        assert result["size"].dtype == pl.Enum

    def test_object_array_categories(self):
        """Object-form categories: use 'value' key, ignore 'label'."""
        df = pl.DataFrame({"fruit": ["apple", "banana", "apple"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="fruit",
                    type=UniversalType.STRING,
                    categories=[
                        {"value": "apple", "label": "Apple"},
                        {"value": "banana", "label": "Banana"},
                        {"value": "orange", "label": "Orange"},
                    ],
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["fruit"].to_list() == ["apple", "banana", "apple"]
        assert result["fruit"].dtype == pl.Categorical

    def test_object_array_categories_ordered(self):
        """Object-form + ordered -> pl.Enum with values in order."""
        df = pl.DataFrame({"level": ["low", "high", "low"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="level",
                    type=UniversalType.STRING,
                    categories=[
                        {"value": "low", "label": "Low"},
                        {"value": "medium", "label": "Medium"},
                        {"value": "high", "label": "High"},
                    ],
                    categories_ordered=True,
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["level"].to_list() == ["low", "high", "low"]
        assert result["level"].dtype == pl.Enum

    def test_categories_with_base_type_cast(self):
        """Categories on a non-string field: base type cast then categorical."""
        df = pl.DataFrame({"score": [1, 2, 3]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="score",
                    type=UniversalType.STRING,
                    categories=["1", "2", "3", "4", "5"],
                    categories_ordered=True,
                ),
            ],
            # Disable missingValues sentinels — default [""] would
            # emit is_in on the Int64 source before the string cast.
            missing_values=[],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["score"].to_list() == ["1", "2", "3"]
        assert result["score"].dtype == pl.Enum

    def test_categories_preserves_null(self):
        """Null values pass through categorical casting."""
        df = pl.DataFrame({"color": ["red", None, "blue"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="color",
                    type=UniversalType.STRING,
                    categories=["red", "blue", "green"],
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["color"].to_list() == ["red", None, "blue"]
        assert result["color"].dtype == pl.Categorical

    def test_categories_ordered_false_is_categorical(self):
        """Explicitly setting categories_ordered=False -> pl.Categorical."""
        df = pl.DataFrame({"tag": ["a", "b", "a"]})
        spec = TypeSpec(
            fields=[
                FieldSpec(
                    name="tag",
                    type=UniversalType.STRING,
                    categories=["a", "b", "c"],
                    categories_ordered=False,
                ),
            ],
        )
        result = ma.relation(df).conform(spec).to_polars()
        assert result["tag"].to_list() == ["a", "b", "a"]
        assert result["tag"].dtype == pl.Categorical
