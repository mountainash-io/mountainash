"""Tests for nested STRUCT (object_fields) casting in the conform pipeline
(item 102, spec §5). Polars-only — see spec §5's Consequence and this
plan's Global Constraints; the cross-backend DtypeMappingError companion
assertion lives in tests/conform/cross_backend/test_relation_conform.py.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.errors import ConformTransformError
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType


class TestStructCastingFlat:
    def test_flat_struct_cast_by_name(self):
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = TableSchema(fields={"addr": FieldDefinition(type=UniversalType.OBJECT, fields={"street": FieldDefinition(type=UniversalType.STRING),
                "zip": FieldDefinition(type=UniversalType.STRING),}),})
        result = ma.relation(df).conform(spec).to_polars()
        assert result.schema["addr"] == pl.Struct({"street": pl.String, "zip": pl.String})
        assert result["addr"].to_list() == [{"street": "Main St", "zip": "12345"}]

    def test_struct_field_matching_is_by_name_not_position(self):
        """Spec §5.2 spike (§13.1): reordered targets match source by name."""
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = TableSchema(fields={"addr": FieldDefinition(type=UniversalType.OBJECT, fields={"zip": FieldDefinition(type=UniversalType.STRING),
                "street": FieldDefinition(type=UniversalType.STRING),}),})
        result = ma.relation(df).conform(spec).to_polars()
        row = result["addr"].to_list()[0]
        assert row["zip"] == "12345"
        assert row["street"] == "Main St"

    def test_inner_type_cast_applied(self):
        """Inner fields are cast, not only structurally wrapped."""
        df = pl.DataFrame([{"stats": {"count": "3", "label": "x"}}])
        spec = TableSchema(fields={"stats": FieldDefinition(type=UniversalType.OBJECT, fields={"count": FieldDefinition(type=UniversalType.INTEGER),
                "label": FieldDefinition(type=UniversalType.STRING),}),})
        result = ma.relation(df).conform(spec).to_polars()
        assert {f.name: f.dtype for f in result.schema["stats"].fields}["count"] == pl.Int64
        assert result["stats"].to_list() == [{"count": 3, "label": "x"}]


class TestStructCastingNested:
    def test_two_level_nested_struct_cast(self):
        df = pl.DataFrame([{"addr": {"street": "Main St", "geo": {"lat": "1.5", "lon": "2.5"}}}])
        spec = TableSchema(fields={"addr": FieldDefinition(type=UniversalType.OBJECT, fields={"street": FieldDefinition(type=UniversalType.STRING),
                "geo": FieldDefinition(type=UniversalType.OBJECT, fields={"lat": FieldDefinition(type=UniversalType.NUMBER),
                    "lon": FieldDefinition(type=UniversalType.NUMBER),}),}),})
        result = ma.relation(df).conform(spec).to_polars()
        expected_dtype = pl.Struct({
            "street": pl.String,
            "geo": pl.Struct({"lat": pl.Float64, "lon": pl.Float64}),
        })
        assert result.schema["addr"] == expected_dtype
        assert result["addr"].to_list() == [{"street": "Main St", "geo": {"lat": 1.5, "lon": 2.5}}]


def test_nested_date_cast_preserves_parent_nulls_and_matches_struct_fields_by_name():
    """Temporal leaves convert recursively without collapsing null parents."""
    from datetime import date

    df = pl.DataFrame(
        {"payload": [
            {"label": "ok", "items": [{"day": "2026-10-12"}, None]},
            None,
            {"label": "empty", "items": []},
        ]},
        schema={"payload": pl.Struct({
            "label": pl.String, "items": pl.List(pl.Struct({"day": pl.String}))
        })},
    )
    spec = TableSchema(fields={"payload": FieldDefinition(type=UniversalType.OBJECT, fields={"items": FieldDefinition(type=UniversalType.ARRAY, element=FieldDefinition(fields = {"day": FieldDefinition(type=UniversalType.DATE),})),
            "label": FieldDefinition(type=UniversalType.STRING),})})
    result = ma.relation(df).conform(spec).to_polars()
    assert result["payload"].to_list() == [
        {"items": [{"day": date(2026, 10, 12)}, None], "label": "ok"},
        None,
        {"items": [], "label": "empty"},
    ]


class TestStructCastingErrorHandling:
    def test_incompatible_inner_type_raises(self):
        """Spec §6/§13.1: incompatible inner type raises."""
        df = pl.DataFrame([{"addr": {"count": "not-a-number"}}])
        spec = TableSchema(fields={"addr": FieldDefinition(type=UniversalType.OBJECT, fields={"count": FieldDefinition(type=UniversalType.INTEGER),}),})
        with pytest.raises(Exception):
            ma.relation(df).conform(spec).to_polars()

    def test_categories_and_object_shape_conflict_is_rejected(self):
        """A concrete string source cannot satisfy a declared OBJECT shape."""
        df = pl.DataFrame({"x": ["a", "b"]})
        spec = TableSchema(fields={"x": FieldDefinition(type=UniversalType.OBJECT,
                      categories=["a", "b"], categories_ordered=False,
                      fields={"never": FieldDefinition(type=UniversalType.STRING)}),})
        with pytest.raises(
            ConformTransformError,
            match=r"invalid object value in field 'x' at row ordinal 0",
        ):
            ma.relation(df).conform(spec).to_polars()
