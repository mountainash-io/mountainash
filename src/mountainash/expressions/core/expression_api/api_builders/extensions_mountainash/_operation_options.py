"""Validation shared by the Unit C structural operation builders."""
from __future__ import annotations

from typing import Any

from mountainash.core.errors import InvalidOptionValueError
from mountainash.typespec.spec import FieldSpec
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour


LIST_ITEM_TYPES = frozenset({"string", "integer", "boolean", "number", "datetime", "date", "time"})


def invalid(method: str, option: str, reason: str) -> None:
    raise InvalidOptionValueError(f"{method}: invalid {option}; {reason}")


def validate_field_name(method: str, field_name: Any) -> str:
    if not isinstance(field_name, str) or not field_name:
        invalid(method, "field_name", "must be a non-empty string")
    return field_name


def validate_failure_behavior(method: str, value: Any) -> CaseFailureBehaviour:
    if not isinstance(value, CaseFailureBehaviour):
        invalid(method, "failure_behavior", "must be CaseFailureBehaviour")
    return value


def validate_fields(method: str, option: str, fields: Any) -> tuple[FieldSpec, ...]:
    if not isinstance(fields, tuple) or not fields:
        invalid(method, option, "must be a non-empty tuple of FieldSpec")
    for index, field in enumerate(fields):
        if not isinstance(field, FieldSpec):
            invalid(method, f"{option}[{index}]", "must be FieldSpec")
    return fields


def validate_item_type(method: str, item_type: Any) -> str:
    if not isinstance(item_type, str) or item_type not in LIST_ITEM_TYPES:
        invalid(method, "item_type", "must be one of the seven Frictionless item types")
    return item_type


def validate_delimiter(method: str, delimiter: Any) -> str:
    if not isinstance(delimiter, str) or not delimiter:
        invalid(method, "delimiter", "must be a non-empty string")
    return delimiter


def validate_categories(method: str, value_type: Any, categories: Any, ordered: Any) -> tuple[Any, ...]:
    if not isinstance(value_type, str) or value_type not in {"string", "integer"}:
        invalid(method, "value_type", "must be string or integer")
    if not isinstance(categories, tuple):
        invalid(method, "categories", "must be a tuple of matching scalar values")
    expected = str if value_type == "string" else int
    for index, value in enumerate(categories):
        valid = isinstance(value, expected) and not (value_type == "integer" and isinstance(value, bool))
        if not valid:
            invalid(method, f"categories[{index}]", f"must be {value_type}")
    if not isinstance(ordered, bool):
        invalid(method, "ordered", "must be bool")
    return categories


GEOPOINT_FORMATS = frozenset({"default", "array", "object"})
GEOPOINT_REPRESENTATIONS = frozenset({"lexical", "native"})
GEOJSON_FORMATS = frozenset({"default", "topojson"})


def validate_geopoint_options(method: str, format: Any, source_representation: Any) -> tuple[str, str]:
    if not isinstance(format, str) or format not in GEOPOINT_FORMATS:
        invalid(method, "format", "must be default, array, or object")
    if not isinstance(source_representation, str) or source_representation not in GEOPOINT_REPRESENTATIONS:
        invalid(method, "source_representation", "must be lexical or native")
    if (format, source_representation) not in {
        ("default", "lexical"),
        ("array", "lexical"),
        ("array", "native"),
        ("object", "native"),
    }:
        invalid(method, "source_representation", "incompatible with format")
    return format, source_representation


def validate_geojson_format(method: str, format: Any) -> str:
    if not isinstance(format, str) or format not in GEOJSON_FORMATS:
        invalid(method, "format", "must be default or topojson")
    return format
