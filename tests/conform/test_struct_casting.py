"""Tests for recursive composed-declaration casting in conform."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.conform.errors import ConformTransformError
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


class TestStructCastingFlat:
    def test_flat_struct_cast_by_name(self):
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = TypeSpec(fields={
            "addr": FieldSpec(fields={
                "street": FieldSpec(type=UniversalType.STRING),
                "zip": FieldSpec(type=UniversalType.STRING),
            }),
        })
        result = ma.relation(df).conform(spec).to_polars()
        assert result.schema["addr"] == pl.Struct({"street": pl.String, "zip": pl.String})
        assert result["addr"].to_list() == [{"street": "Main St", "zip": "12345"}]

    def test_struct_field_matching_is_by_name_not_position(self):
        """Spec §5.2 spike (§13.1): reordered targets match source by name."""
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = TypeSpec(fields={
            "addr": FieldSpec(fields={
                "zip": FieldSpec(type=UniversalType.STRING),
                "street": FieldSpec(type=UniversalType.STRING),
            }),
        })
        result = ma.relation(df).conform(spec).to_polars()
        row = result["addr"].to_list()[0]
        assert row["zip"] == "12345"
        assert row["street"] == "Main St"

    def test_inner_type_cast_applied(self):
        """Inner fields are cast, not only structurally wrapped."""
        df = pl.DataFrame([{"stats": {"count": "3", "label": "x"}}])
        spec = TypeSpec(fields={
            "stats": FieldSpec(fields={
                "count": FieldSpec(type=UniversalType.INTEGER),
                "label": FieldSpec(type=UniversalType.STRING),
            }),
        })
        result = ma.relation(df).conform(spec).to_polars()
        assert {f.name: f.dtype for f in result.schema["stats"].fields}["count"] == pl.Int64
        assert result["stats"].to_list() == [{"count": 3, "label": "x"}]


class TestStructCastingNested:
    def test_two_level_nested_struct_cast(self):
        df = pl.DataFrame([{"addr": {"street": "Main St", "geo": {"lat": "1.5", "lon": "2.5"}}}])
        spec = TypeSpec(fields={
            "addr": FieldSpec(fields={
                "street": FieldSpec(type=UniversalType.STRING),
                "geo": FieldSpec(fields={
                    "lat": FieldSpec(type=UniversalType.NUMBER),
                    "lon": FieldSpec(type=UniversalType.NUMBER),
                }),
            }),
        })
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
    spec = TypeSpec(fields={
        "payload": FieldSpec(fields={
            "items": FieldSpec(element=FieldSpec(fields={
                "day": FieldSpec(type=UniversalType.DATE),
            })),
            "label": FieldSpec(type=UniversalType.STRING),
        }),
    })
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
        spec = TypeSpec(fields={
            "addr": FieldSpec(fields={
                "count": FieldSpec(type=UniversalType.INTEGER),
            }),
        })
        with pytest.raises(Exception):
            ma.relation(df).conform(spec).to_polars()

    def test_categories_and_object_shape_conflict_is_rejected(self):
        """A concrete string source cannot satisfy a declared OBJECT shape."""
        df = pl.DataFrame({"x": ["a", "b"]})
        spec = TypeSpec(fields={
            "x": FieldSpec(
                fields={"never": FieldSpec(type=UniversalType.STRING)},
                categories=["a", "b"], categories_ordered=False,
            ),
        })
        with pytest.raises(
            ConformTransformError,
            match=r"invalid object value in field 'x' at row ordinal 0",
        ):
            ma.relation(df).conform(spec).to_polars()


def test_composed_declarations_convert_nested_values_and_keep_container_scope():
    df = pl.DataFrame([{
        "raw": {"quantity": "2", "missing": None},
        "items": [{"quantity": "-3"}, None],
    }])
    quantity = FieldSpec(type=UniversalType.INTEGER, minimum=0, null_fill=7)
    record = FieldSpec(fields={
        "quantity": quantity,
        "missing": FieldSpec(type=UniversalType.INTEGER, null_fill=7),
    })
    spec = TypeSpec(fields={
        "record": record.variant(rename_from="raw"),
        "items": FieldSpec(
            element=FieldSpec(fields={"quantity": quantity}),
        ),
    })
    result = ma.relation(df).conform(spec).to_polars()
    assert result.columns == ["record", "items"]
    assert result["record"].to_list() == [{"quantity": 2, "missing": 7}]
    assert result["items"].to_list() == [[{"quantity": -3}, None]]
