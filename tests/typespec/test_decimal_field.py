"""FieldDefinition.dtype (DecimalDtype): declaration, persistence, lowering, extraction, comparison (item 241)."""
from __future__ import annotations

import ibis
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

import mountainash as ma
from mountainash.typespec import FieldDefinition, TableSchema, UniversalType
from mountainash.typespec.converters import to_arrow_schema, to_polars_schema
from mountainash.typespec.errors import (
    IncompatibleFieldPropertiesError,
    InvalidDescriptorStructure,
    InvalidDtypeDeclaration,
)
from mountainash.typespec.extraction import extract_from_dataframe
from mountainash.typespec.frictionless import (
    table_schema_from_frictionless,
    table_schema_to_frictionless,
)
from mountainash.typespec.spec import compare_specs

D103 = ma.DecimalDtype(precision=10, scale=3)


def _schema(**fields):
    return TableSchema(fields=fields)


def _number(**kwargs):
    return FieldDefinition(type=UniversalType.NUMBER, **kwargs)


class TestFieldDefinitionDecimal:
    @pytest.mark.parametrize(
        "kwargs,error",
        [
            ({"type": UniversalType.STRING}, IncompatibleFieldPropertiesError),
            ({"type": UniversalType.INTEGER}, IncompatibleFieldPropertiesError),
            ({"type": UniversalType.NUMBER, "categories": [1.5]}, InvalidDtypeDeclaration),
        ],
    )
    def test_rejected_combinations(self, kwargs, error):
        with pytest.raises(error):
            FieldDefinition(dtype=D103, **kwargs)

    @pytest.mark.parametrize("mode", ["bankers", 1])
    def test_invalid_rounding_declaration(self, mode):
        with pytest.raises(InvalidDtypeDeclaration):
            _number(dtype=D103, rounding=mode)

    def test_rounding_requires_decimal_target(self):
        with pytest.raises(InvalidDtypeDeclaration):
            _number(rounding="half_to_even")


class TestCompareSpecsDecimal:
    def test_precision_scale_difference_is_a_type_change(self):
        a = _schema(x=_number(dtype=D103))
        b = _schema(x=_number(dtype=ma.DecimalDtype(precision=12, scale=4)))
        assert "x" in compare_specs(a, b).type_changes

    def test_declared_decimal_against_plain_number_is_a_type_change(self):
        a = _schema(x=_number(dtype=D103))
        b = _schema(x=_number())
        assert "x" in compare_specs(a, b).type_changes
        assert "x" in compare_specs(b, a).type_changes

    def test_equal_decimals_do_not_differ(self):
        a = _schema(x=_number(dtype=D103))
        b = _schema(x=_number(dtype=D103))
        assert not compare_specs(a, b).type_changes

    def test_rounding_is_not_type_incompatibility(self):
        left = _schema(x=_number(dtype=D103, rounding="half_to_even"))
        right = _schema(x=_number(dtype=D103, rounding="to_zero"))
        result = compare_specs(left, right)
        assert result.is_compatible and not result.type_changes

    def test_extra_actual_field_still_compatible(self):
        a = _schema(x=_number())
        b = _schema(x=_number(), y=FieldDefinition(type=UniversalType.STRING))
        diff = compare_specs(b, a)
        assert diff.is_compatible is True
        assert diff.removed_fields == ["y"] and not diff.type_changes

    def test_geopoint_formats_unchanged(self):
        a = _schema(p=FieldDefinition(type=UniversalType.GEOPOINT, format="default"))
        b = _schema(p=FieldDefinition(type=UniversalType.GEOPOINT, format="array"))
        assert not compare_specs(a, b).type_changes


class TestFrictionlessDecimal:
    def test_round_trip_including_nested(self):
        child = _number(dtype=D103, rounding="half_to_even")
        spec = _schema(
            amount=child,
            rec=FieldDefinition(type=UniversalType.OBJECT, fields={"amount": child}),
            items=FieldDefinition(
                type=UniversalType.ARRAY,
                element=FieldDefinition(type=UniversalType.OBJECT, fields={"amount": child}),
            ),
        )
        desc = table_schema_to_frictionless(spec)
        assert desc["fields"][0]["type"] == "number"
        assert desc["fields"][0]["x-mountainash"]["dtype"] == {
            "kind": "decimal", "precision": 10, "scale": 3,
        }
        back = table_schema_from_frictionless(desc)
        assert list(back.fields) == ["amount", "rec", "items"]
        nested = [
            back.fields["amount"],
            back.fields["rec"].fields["amount"],
            back.fields["items"].element.fields["amount"],
        ]
        for restored in nested:
            assert restored.dtype == D103
            assert restored.rounding == "half_to_even"

    @pytest.mark.parametrize("mode", ["half_to_even", "half_away_from_zero", "to_zero"])
    def test_rounding_descriptor_contract(self, mode):
        descriptor = {"fields": [{
            "name": "amount", "type": "number",
            "x-mountainash": {
                "dtype": {"kind": "decimal", "precision": 5, "scale": 2},
                "rounding": mode,
            },
        }]}
        spec = table_schema_from_frictionless(descriptor)
        assert spec.fields["amount"].rounding == mode
        assert table_schema_to_frictionless(spec) == descriptor

    @pytest.mark.parametrize("rounding_extension", [{}, {"rounding": None}])
    def test_legacy_rounding_is_omitted_on_write(self, rounding_extension):
        dtype = {"kind": "decimal", "precision": 10, "scale": 3}
        descriptor = {"fields": [{
            "name": "x", "type": "number",
            "x-mountainash": {"dtype": dtype, **rounding_extension},
        }]}
        spec = table_schema_from_frictionless(descriptor)
        assert spec.fields["x"].rounding is None
        assert spec.fields["x"].dtype == D103
        assert table_schema_to_frictionless(spec) == {"fields": [{
            "name": "x", "type": "number", "x-mountainash": {"dtype": dtype},
        }]}

    @pytest.mark.parametrize("extension", [
        {"dtype": {"kind": "decimal", "precision": 10, "scale": 3}, "rounding": "bankers"},
        {"rounding": "half_to_even"},
    ])
    def test_invalid_rounding_descriptor(self, extension):
        with pytest.raises(InvalidDtypeDeclaration):
            table_schema_from_frictionless({"fields": [{
                "name": "x", "type": "number", "x-mountainash": extension,
            }]})

    def test_plain_number_emits_no_dtype_extension(self):
        desc = table_schema_to_frictionless(_schema(a=_number()))
        assert "x-mountainash" not in desc["fields"][0]

    @pytest.mark.parametrize(
        "bad",
        [
            {"kind": "decimel", "precision": 10, "scale": 3},
            {"kind": "decimal", "precision": 10},
            {"kind": "decimal", "precision": "10", "scale": 3},
            {"kind": "decimal", "precision": 39, "scale": 3},
            {"precision": 10, "scale": 3},
        ],
    )
    def test_malformed_dtype_extension_raises(self, bad):
        """Our own x-mountainash.dtype is validated on load, never silently dropped."""
        desc = {"fields": [{"name": "amount", "type": "number", "x-mountainash": {"dtype": bad}}]}
        with pytest.raises(InvalidDtypeDeclaration):
            table_schema_from_frictionless(desc)

    def test_string_dtype_extension_reports_its_descriptor_location(self):
        desc = {"fields": [{
            "name": "amount", "type": "number",
            "x-mountainash": {"dtype": "decimal(10,3)"},
        }]}
        with pytest.raises(InvalidDescriptorStructure) as caught:
            table_schema_from_frictionless(desc)
        assert caught.value.descriptor_path == "$.fields[0].x-mountainash.dtype"

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
            table_schema_from_frictionless(desc)


class TestConvertersDecimal:
    def test_lowering(self):
        spec = _schema(a=_number(dtype=D103))
        assert to_polars_schema(spec)["a"] == pl.Decimal(10, 3)
        assert to_arrow_schema(spec).field("a").type == pa.decimal128(10, 3)

    def test_plain_number_lowering_unchanged(self):
        assert to_polars_schema(_schema(a=_number()))["a"] == pl.Float64


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
    }[backend_name]()


@pytest.mark.parametrize(
    "backend_name",
    ["polars", "pandas", "narwhals-polars", "pyarrow", "ibis-duckdb"],
)
def test_decimal_extraction_per_backend(backend_name):
    """p/s survives native schema extraction on each backend family (schema only, no cast)."""
    field = extract_from_dataframe(_native_decimal_frame(backend_name)).fields["a"]
    assert field.type is UniversalType.NUMBER
    assert field.dtype == ma.DecimalDtype(precision=12, scale=4)
    assert field.rounding is None


def test_decimal_extraction_survives_a_round_trip_through_lowering():
    df = pl.DataFrame({"a": pl.Series([None], dtype=pl.Decimal(12, 4))})
    spec = extract_from_dataframe(df)
    assert to_polars_schema(spec)["a"] == pl.Decimal(12, 4)
