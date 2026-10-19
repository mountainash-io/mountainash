"""Logical values shared by field authoring and JSON declaration interchange."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from datetime import date, datetime, time
from decimal import Decimal
import json
from typing import TYPE_CHECKING, Any

from mountainash.typespec.temporal import parse_default_datetime, parse_temporal_any
from mountainash.typespec.universal_types import UniversalType, parse_universal

if TYPE_CHECKING:
    from mountainash.typespec.spec import FieldSpec


_VALUE_CONSTRAINTS = (
    "minimum", "maximum", "exclusive_minimum", "exclusive_maximum", "eq", "ne",
)
_SEQUENCE_CONSTRAINTS = ("enum", "notin")


def _element(field: FieldSpec) -> FieldSpec | None:
    from mountainash.typespec.converters import _collection_item
    from mountainash.typespec.spec import FieldSpec

    element = _collection_item(field)
    if element is None and field.type is UniversalType.LIST and field.item_type is not None:
        return FieldSpec(type=parse_universal(field.item_type))
    return element


def normalize_field_value(field: FieldSpec, value: Any) -> Any:
    """Interpret a requirement/conversion value, never a text metadata property."""
    if value is None:
        return None
    kind = field.type
    if kind is UniversalType.OBJECT:
        from mountainash.typespec.converters import declared_fields

        if isinstance(value, str):
            value = json.loads(value)
        children = declared_fields(field)
        if isinstance(value, Mapping):
            return {
                name: normalize_field_value(children[name], item) if name in children else item
                for name, item in value.items()
            }
    elif kind in (UniversalType.ARRAY, UniversalType.LIST):
        if isinstance(value, str):
            value = value.split(field.delimiter or ",") if kind is UniversalType.LIST else json.loads(value)
        element = _element(field)
        if isinstance(value, (list, tuple)) and element is not None:
            return tuple(normalize_field_value(element, item) for item in value)
    elif (
        kind is UniversalType.DATETIME and field.format == "default"
        and isinstance(value, (str, date, time, datetime))
    ):
        return parse_default_datetime(value)
    elif kind in (UniversalType.DATE, UniversalType.TIME, UniversalType.DATETIME) and isinstance(value, str):
        if field.format == "any":
            return parse_temporal_any(value, kind=kind.value)
        if field.format == "default":
            return date.fromisoformat(value) if kind is UniversalType.DATE else time.fromisoformat(value)
        parsed = datetime.strptime(value, field.format)
        return parsed.date() if kind is UniversalType.DATE else parsed.timetz() if kind is UniversalType.TIME else parsed
    elif kind in (UniversalType.INTEGER, UniversalType.NUMBER) and isinstance(value, str):
        if field.group_char:
            value = value.replace(field.group_char, "")
        if field.decimal_char and field.decimal_char != ".":
            value = value.replace(field.decimal_char, ".")
        return Decimal(value)
    elif kind is UniversalType.BOOLEAN and isinstance(value, str):
        if value in (field.true_values if field.true_values is not None else ("true", "True", "TRUE", "1")):
            return True
        if value in (field.false_values if field.false_values is not None else ("false", "False", "FALSE", "0")):
            return False
    return value


def normalize_field_values(field: FieldSpec) -> None:
    """Normalize once while an immutable FieldSpec is being constructed."""
    from mountainash.typespec.spec import _own_value

    constraints = field.constraints
    if constraints is not None:
        changes = {}
        for name in _VALUE_CONSTRAINTS:
            original = getattr(constraints, name)
            normalized = normalize_field_value(field, original)
            if normalized is not original:
                changes[name] = normalized
        for name in _SEQUENCE_CONSTRAINTS:
            original = getattr(constraints, name)
            if original is not None:
                normalized = tuple(normalize_field_value(field, item) for item in original)
                if any(left is not right for left, right in zip(original, normalized, strict=True)):
                    changes[name] = normalized
        if changes:
            object.__setattr__(field, "constraints", replace(constraints, **changes))
    if field.null_fill is not None:
        try:
            normalized = normalize_field_value(field, field.null_fill)
        except (TypeError, ValueError, ArithmeticError):
            # A fill is an input to the existing cast policy, not a requirement.
            # Invalid lexical fills may become null or be ignored by that policy.
            normalized = field.null_fill
        object.__setattr__(field, "null_fill", _own_value(normalized))


def json_value(value: Any) -> Any:
    """Copy the JSON value vocabulary, rejecting opaque untyped Python payloads."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    raise ValueError(f"{type(value).__name__} has no supported JSON representation")


def field_value_to_json(field: FieldSpec, value: Any) -> Any:
    """Encode typed values losslessly; formatting errors belong to persistence."""
    if isinstance(value, (date, time, datetime, Decimal)):
        if isinstance(value, Decimal):
            encoded = str(value)
            if field.decimal_char and field.decimal_char != ".":
                encoded = encoded.replace(".", field.decimal_char)
        else:
            encoded = value.isoformat() if field.format in ("default", "any") else value.strftime(field.format)
        try:
            restored = normalize_field_value(field, encoded)
        except (ValueError, TypeError, ArithmeticError) as exc:
            raise ValueError("value cannot be represented under the declared type/format") from exc
        if type(restored) is not type(value) or restored != value:
            raise ValueError("value cannot be represented losslessly under the declared type/format")
        return encoded
    if isinstance(value, Mapping) and field.type is UniversalType.OBJECT:
        from mountainash.typespec.converters import declared_fields

        children = declared_fields(field)
        return {
            key: field_value_to_json(children[key], item) if key in children else json_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)) and field.type in (UniversalType.ARRAY, UniversalType.LIST):
        element = _element(field)
        return [field_value_to_json(element, item) if element is not None else json_value(item) for item in value]
    return json_value(value)
