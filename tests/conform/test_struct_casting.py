"""Tests for nested STRUCT (object_fields) casting in the conform pipeline
(item 102, spec §5). Polars-only — see spec §5's Consequence and this
plan's Global Constraints; the cross-backend DtypeMappingError companion
assertion lives in tests/conform/cross_backend/test_relation_conform.py.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestStructCastingFlat:
    def test_flat_struct_cast_by_name(self):
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="street", type=UniversalType.STRING),
                FieldSpec(name="zip", type=UniversalType.STRING),
            ]),
        ])
        result = ma.relation(df).conform(spec).to_polars()
        assert result.schema["addr"] == pl.Struct({"street": pl.String, "zip": pl.String})
        assert result["addr"].to_list() == [{"street": "Main St", "zip": "12345"}]

    def test_struct_field_matching_is_by_name_not_position(self):
        """Spec §5.2 spike (§13.1): reordered targets match source by name."""
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="zip", type=UniversalType.STRING),
                FieldSpec(name="street", type=UniversalType.STRING),
            ]),
        ])
        result = ma.relation(df).conform(spec).to_polars()
        row = result["addr"].to_list()[0]
        assert row["zip"] == "12345"
        assert row["street"] == "Main St"

    def test_inner_type_cast_applied(self):
        """Inner fields are cast, not only structurally wrapped."""
        df = pl.DataFrame([{"stats": {"count": "3", "label": "x"}}])
        spec = TypeSpec(fields=[
            FieldSpec(name="stats", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="count", type=UniversalType.INTEGER),
                FieldSpec(name="label", type=UniversalType.STRING),
            ]),
        ])
        result = ma.relation(df).conform(spec).to_polars()
        assert {f.name: f.dtype for f in result.schema["stats"].fields}["count"] == pl.Int64
        assert result["stats"].to_list() == [{"count": 3, "label": "x"}]


class TestStructCastingNested:
    def test_two_level_nested_struct_cast(self):
        df = pl.DataFrame([{"addr": {"street": "Main St", "geo": {"lat": "1.5", "lon": "2.5"}}}])
        spec = TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="street", type=UniversalType.STRING),
                FieldSpec(name="geo", type=UniversalType.OBJECT, object_fields=[
                    FieldSpec(name="lat", type=UniversalType.NUMBER),
                    FieldSpec(name="lon", type=UniversalType.NUMBER),
                ]),
            ]),
        ])
        result = ma.relation(df).conform(spec).to_polars()
        expected_dtype = pl.Struct({
            "street": pl.String,
            "geo": pl.Struct({"lat": pl.Float64, "lon": pl.Float64}),
        })
        assert result.schema["addr"] == expected_dtype
        assert result["addr"].to_list() == [{"street": "Main St", "geo": {"lat": 1.5, "lon": 2.5}}]


class TestStructCastingErrorHandling:
    def test_incompatible_inner_type_raises(self):
        """Spec §6/§13.1: incompatible inner type raises."""
        df = pl.DataFrame([{"addr": {"count": "not-a-number"}}])
        spec = TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="count", type=UniversalType.INTEGER),
            ]),
        ])
        with pytest.raises(Exception):
            ma.relation(df).conform(spec).to_polars()

    def test_categories_and_object_shape_conflict_is_rejected(self):
        """A concrete string source cannot satisfy a declared OBJECT shape."""
        df = pl.DataFrame({"x": ["a", "b"]})
        spec = TypeSpec(fields=[
            FieldSpec(name="x", type=UniversalType.OBJECT,
                      categories=["a", "b"], categories_ordered=False,
                      object_fields=[FieldSpec(name="never", type=UniversalType.STRING)]),
        ])
        with pytest.raises(Exception, match="incompatible source type"):
            ma.relation(df).conform(spec).to_polars()
