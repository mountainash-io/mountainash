"""FieldSpec.dtype (DecimalDtype): declaration, persistence, lowering, extraction, comparison (item 241)."""
from __future__ import annotations

import ibis
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
from mountainash.typespec.converters import to_arrow_schema, to_polars_schema
from mountainash.typespec.errors import (
    IncompatibleFieldPropertiesError,
    InvalidDtypeDeclaration,
)
from mountainash.typespec.extraction import extract_from_dataframe
from mountainash.typespec.frictionless import (
    typespec_from_frictionless,
    typespec_to_frictionless,
)
from mountainash.typespec.spec import compare_specs

D103 = ma.DecimalDtype(precision=10, scale=3)


class TestFieldSpecDecimal:
    def test_number_with_dtype(self):
        assert FieldSpec(name="a", type=UniversalType.NUMBER, dtype=D103).dtype == D103

    def test_default_is_none(self):
        assert FieldSpec(name="a", type=UniversalType.NUMBER).dtype is None

    @pytest.mark.parametrize(
        "kwargs,error",
        [
            ({"type": UniversalType.STRING}, IncompatibleFieldPropertiesError),
            ({"type": UniversalType.INTEGER}, IncompatibleFieldPropertiesError),
            ({"type": UniversalType.NUMBER, "backend_type": "Float64"}, InvalidDtypeDeclaration),
            ({"type": UniversalType.NUMBER, "categories": [1.5]}, InvalidDtypeDeclaration),
        ],
    )
    def test_rejected_combinations(self, kwargs, error):
        with pytest.raises(error):
            FieldSpec(name="a", dtype=D103, **kwargs)


class TestCompareSpecsDecimal:
    def test_precision_scale_difference_is_a_type_change(self):
        a = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER, dtype=D103)])
        b = TypeSpec(
            fields=[FieldSpec(name="x", type=UniversalType.NUMBER, dtype=ma.DecimalDtype(precision=12, scale=4))]
        )
        assert "x" in compare_specs(a, b).type_changes

    def test_declared_decimal_against_plain_number_is_a_type_change(self):
        a = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER, dtype=D103)])
        b = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER)])
        assert "x" in compare_specs(a, b).type_changes
        assert "x" in compare_specs(b, a).type_changes

    def test_equal_decimals_do_not_differ(self):
        a = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER, dtype=D103)])
        b = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER, dtype=D103)])
        assert not compare_specs(a, b).type_changes

    def test_extra_actual_field_still_compatible(self):
        # Baseline behaviour measured on develop, must be unchanged.
        a = TypeSpec(fields=[FieldSpec(name="x", type=UniversalType.NUMBER)])
        b = TypeSpec(
            fields=[
                FieldSpec(name="x", type=UniversalType.NUMBER),
                FieldSpec(name="y", type=UniversalType.STRING),
            ]
        )
        diff = compare_specs(b, a)
        assert diff.is_compatible is True
        assert diff.removed_fields == ["y"] and not diff.type_changes

    def test_geopoint_formats_unchanged(self):
        a = TypeSpec(fields=[FieldSpec(name="p", type=UniversalType.GEOPOINT, format="default")])
        b = TypeSpec(fields=[FieldSpec(name="p", type=UniversalType.GEOPOINT, format="array")])
        assert not compare_specs(a, b).type_changes


class TestFrictionlessDecimal:
    def test_round_trip_including_nested(self):
        child = FieldSpec(name="amount", type=UniversalType.NUMBER, dtype=D103)
        spec = TypeSpec(
            fields=[
                child,
                FieldSpec(name="rec", type=UniversalType.OBJECT, object_fields=[child]),
                FieldSpec(name="items", type=UniversalType.ARRAY, item_object_fields=[child]),
            ]
        )
        desc = typespec_to_frictionless(spec)
        assert desc["fields"][0]["type"] == "number"
        assert desc["fields"][0]["x-mountainash"]["dtype"] == {
            "kind": "decimal", "precision": 10, "scale": 3,
        }
        back = typespec_from_frictionless(desc)
        assert back.fields[0].dtype == D103
        assert back.fields[1].object_fields[0].dtype == D103
        assert back.fields[2].item_object_fields[0].dtype == D103

    def test_plain_number_emits_no_dtype_extension(self):
        desc = typespec_to_frictionless(
            TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.NUMBER)])
        )
        assert "x-mountainash" not in desc["fields"][0]

    @pytest.mark.parametrize(
        "bad",
        [
            {"kind": "decimel", "precision": 10, "scale": 3},
            {"kind": "decimal", "precision": 10},
            {"kind": "decimal", "precision": "10", "scale": 3},
            {"kind": "decimal", "precision": 39, "scale": 3},
            {"precision": 10, "scale": 3},
            "decimal(10,3)",
        ],
    )
    def test_malformed_dtype_extension_raises(self, bad):
        """Our own x-mountainash.dtype is validated on load, never silently dropped."""
        desc = {"fields": [{"name": "amount", "type": "number", "x-mountainash": {"dtype": bad}}]}
        with pytest.raises(InvalidDtypeDeclaration):
            typespec_from_frictionless(desc)

    def test_dtype_on_a_non_number_field_raises_on_load(self):
        desc = {
            "fields": [
                {
                    "name": "a",
                    "type": "string",
                    "x-mountainash": {"dtype": {"kind": "decimal", "precision": 10, "scale": 3}},
                }
            ]
        }
        with pytest.raises(IncompatibleFieldPropertiesError):
            typespec_from_frictionless(desc)


class TestConvertersDecimal:
    def test_lowering(self):
        spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.NUMBER, dtype=D103)])
        assert to_polars_schema(spec)["a"] == pl.Decimal(10, 3)
        assert to_arrow_schema(spec).field("a").type == pa.decimal128(10, 3)

    def test_plain_number_lowering_unchanged(self):
        spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.NUMBER)])
        assert to_polars_schema(spec)["a"] == pl.Float64


def _native_decimal_frame(backend_name):
    """Test setup only: one Arrow table with a decimal(12,4) column, built natively per backend.

    BackendDataFrameFactory.create builds from plain Python data and has no typed/Arrow constructor.
    """
    table = pa.table({"a": pa.array([None], pa.decimal128(12, 4))})
    return {
        "polars": lambda: pl.from_arrow(table),
        "pandas": lambda: table.to_pandas(types_mapper=pd.ArrowDtype),
        "narwhals-polars": lambda: nw.from_native(pl.from_arrow(table)),
        "pyarrow": lambda: table,
        "ibis-duckdb": lambda: ibis.duckdb.connect().create_table("t", table),
        "ibis-polars": lambda: ibis.polars.connect().create_table("t", pl.from_arrow(table)),
    }[backend_name]()


@pytest.mark.parametrize(
    "backend_name",
    ["polars", "pandas", "narwhals-polars", "pyarrow", "ibis-duckdb", "ibis-polars"],
)
def test_decimal_extraction_per_backend(backend_name):
    """p/s survives native schema extraction on each backend family (schema only, no cast)."""
    field = extract_from_dataframe(_native_decimal_frame(backend_name)).fields[0]
    assert field.type is UniversalType.NUMBER
    assert field.dtype == ma.DecimalDtype(precision=12, scale=4)
    assert field.backend_type is None


def test_decimal_extraction_survives_a_round_trip_through_lowering():
    df = pl.DataFrame({"a": pl.Series([None], dtype=pl.Decimal(12, 4))})
    spec = extract_from_dataframe(df)
    assert to_polars_schema(spec)["a"] == pl.Decimal(12, 4)
