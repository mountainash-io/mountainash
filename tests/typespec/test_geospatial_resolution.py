"""resolve_field_canonical() — the field-aware canonical resolver for the
format-dependent geospatial types (item 113 Unit B, Task 2, spec §8.3).

GEOPOINT's canonical shape depends on FieldDefinition.format ("default" -> STRING,
"array" -> LIST, "object" -> STRUCT); a bare to_canonical(GEOPOINT) call has
no field context and must raise AmbiguousGeospatialTypeError instead of
guessing. GEOJSON always resolves to canonical JSON regardless of format
("default"/"topojson" are both JSON objects per the Frictionless spec).
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.dtypes import SchemaTypeStatus, TypeTarget
from mountainash.typespec.converters import resolve_field_canonical, resolve_field_type
from mountainash.typespec.errors import InvalidGeospatialFormatError
from mountainash.typespec.spec import FieldDefinition
from mountainash.typespec.universal_types import UniversalType as U


class TestGeopointFormatResolution:
    @pytest.mark.parametrize(
        "format_,expected",
        [("default", D.STRING), ("array", D.LIST), ("object", D.STRUCT)],
    )
    def test_geopoint_resolves_by_format(self, format_: str, expected: D) -> None:
        assert resolve_field_canonical(
            FieldDefinition(type=U.GEOPOINT, format=format_)
        ) is expected


class TestGeojsonFormatResolution:
    @pytest.mark.parametrize("format_", ["default", "topojson"])
    def test_geojson_resolves_to_json(self, format_: str) -> None:
        assert resolve_field_canonical(
            FieldDefinition(type=U.GEOJSON, format=format_)
        ) is D.JSON


class TestInvalidGeospatialFormats:
    @pytest.mark.parametrize(
        "field",
        [
            FieldDefinition(type=U.GEOPOINT, format="wkt"),
            FieldDefinition(type=U.GEOJSON, format="object"),
        ],
    )
    def test_invalid_geospatial_formats_are_typed(self, field: FieldDefinition) -> None:
        with pytest.raises(InvalidGeospatialFormatError):
            resolve_field_canonical(field)

    def test_invalid_geopoint_format_names_field_and_allowed_set(self) -> None:
        with pytest.raises(InvalidGeospatialFormatError) as exc_info:
            resolve_field_type(
                FieldDefinition(type=U.GEOPOINT, format="wkt"),
                source=None, target=TypeTarget.POLARS, path=("point",),
            )
        err = exc_info.value
        assert err.field_name == "point"
        assert err.universal_type is U.GEOPOINT
        assert err.rejected_format == "wkt"
        assert err.allowed_formats == ["array", "default", "object"]

    def test_invalid_geojson_format_names_field_and_allowed_set(self) -> None:
        with pytest.raises(InvalidGeospatialFormatError) as exc_info:
            resolve_field_type(
                FieldDefinition(type=U.GEOJSON, format="object"),
                source=None, target=TypeTarget.POLARS, path=("geometry",),
            )
        err = exc_info.value
        assert err.field_name == "geometry"
        assert err.universal_type is U.GEOJSON
        assert err.rejected_format == "object"
        assert err.allowed_formats == ["default", "topojson"]

    @pytest.mark.parametrize(
        "field",
        [
            FieldDefinition(type=U.GEOPOINT, format=[]),
            FieldDefinition(type=U.GEOJSON, format={"format": "json"}),
        ],
    )
    def test_unhashable_geospatial_formats_are_typed(self, field: FieldDefinition) -> None:
        with pytest.raises(InvalidGeospatialFormatError) as exc_info:
            resolve_field_canonical(field)
        assert exc_info.value.rejected_format is field.format


class TestNonGeospatialDelegatesToCanonical:
    """Every other UniversalType delegates unchanged to to_canonical()."""

    def test_string_field(self) -> None:
        assert resolve_field_canonical(FieldDefinition(type=U.STRING)) is D.STRING

    def test_integer_field(self) -> None:
        assert resolve_field_canonical(FieldDefinition(type=U.INTEGER)) is D.I64

    def test_any_field_is_unconstrained(self) -> None:
        assert resolve_field_canonical(FieldDefinition(type=U.ANY)) is SchemaTypeStatus.UNCONSTRAINED

    def test_list_field(self) -> None:
        assert resolve_field_canonical(FieldDefinition(type=U.LIST)) is D.LIST
