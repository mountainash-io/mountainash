from __future__ import annotations

import importlib
import mountainash
import mountainash.exceptions as ma_exceptions

from mountainash import MountainashError
from mountainash.exceptions import (
    IncompatibleFieldPropertiesError,
    InvalidFieldMatchDeclaration,
    InvalidGeospatialFormatError,
    InvalidKeyShapeError,
    TypeSpecError,
)
from mountainash.typespec import UniversalType

# Use importlib to avoid shadowing by the typespec() function in mountainash.__init__
ma_typespec = importlib.import_module("mountainash.typespec")


def test_typespec_error_family_export_surfaces() -> None:
    assert issubclass(TypeSpecError, MountainashError)
    assert issubclass(TypeSpecError, ValueError)
    names = {
        "TypeSpecError",
        "AmbiguousGeospatialTypeError",
        "InvalidGeospatialFormatError",
        "InvalidKeyShapeError",
        "IncompatibleFieldPropertiesError",
        "InvalidFieldMatchDeclaration",
    }
    for name in names:
        assert getattr(ma_exceptions, name) is getattr(ma_typespec, name)
        assert not hasattr(mountainash, name)


def test_invalid_geospatial_format_exposes_context() -> None:
    error = InvalidGeospatialFormatError(
        "point", UniversalType.STRING, "wkt", ["array", "default", "object"]
    )
    assert error.field_name == "point"
    assert error.universal_type is UniversalType.STRING
    assert error.rejected_format == "wkt"
    assert error.allowed_formats == ["array", "default", "object"]
    assert "wkt" in str(error)


def test_invalid_key_shape_exposes_context() -> None:
    error = InvalidKeyShapeError("primary_key", "id", "list[str]")
    assert error.field_name == "primary_key"
    assert error.rejected_value == "id"
    assert error.required_form == "list[str]"


def test_incompatible_field_properties_exposes_context() -> None:
    error = IncompatibleFieldPropertiesError(
        "items", "item_type", UniversalType.STRING, (UniversalType.ARRAY,)
    )
    assert error.field_name == "items"
    assert error.property_name == "item_type"
    assert error.actual_type is UniversalType.STRING
    assert error.required_types == (UniversalType.ARRAY,)


def test_invalid_field_match_declaration_exposes_both_locations() -> None:
    error = InvalidFieldMatchDeclaration("subset", "open", "both locations are present")
    assert error.standard_value == "subset"
    assert error.extension_value == "open"
    assert error.reason == "both locations are present"
