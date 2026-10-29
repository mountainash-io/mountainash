"""
Frictionless Table Schema import/export for TableSchema.

Provides the typed codec over shared declarations:
- table_schema_to_frictionless(schema) → dict
- table_schema_from_frictionless(data) → TableSchema
- migrate_nested_field_declarations(descriptor) → dict (explicit, pure)
- FrictionlessSchemaCodec: SchemaCodec decode/encode over the same functions

One recursive body codec serves named fields (table fields, struct members) and
unnamed collection elements. Standard keys and constraints keep their standard
locations; Mountainash extensions (rename_from, null_fill, severity, extended
requirements, nested shape) live under the ``x-mountainash`` namespace key,
following the Frictionless custom extension convention. The codec translates
declarations; it never interprets execution semantics and performs no file,
network or reference resolution.

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from datetime import date, datetime, time
from decimal import Decimal
from functools import cache
from importlib.resources import files
from dataclasses import replace
from typing import Any, Callable, Dict, List, Optional

from jsonschema import Draft7Validator
from jsonschema.validators import extend

from mountainash.conform.contract import validate_contract_dict

from mountainash.core.dtypes import (
    ArrayDtype, DecimalDtype, DurationDtype, ListDtype, MountainashDtype,
    NativeDtype, SchemaTypeStatus, StructDtype, TimeDtype, TimestampDtype,
    resolve_dtype_parameters,
)
from mountainash.core.dtypes.errors import UnknownDtypeError

from .errors import (
    InvalidDescriptorStructure, InvalidDtypeDeclaration, InvalidFieldMatchDeclaration,
    InvalidKeyShapeError,
)
from .frictionless_invariants import (
    InvariantLocation,
    parse_foreign_keys_at,
    reject_typed_profile_at,
)
from .protocols import SchemaCodec
from .spec import (
    FieldConstraints,
    FieldDefinition,
    ForeignKey,
    ForeignKeyReference,
    LabeledValue,
    MissingValue,
    TableSchema,
)
from .temporal import parse_default_datetime, parse_temporal_any
from .universal_types import UniversalType, parse_universal


# The five standard operational field-match modes. ``open`` is the Mountainash
# extension mode, serialized only under ``x-mountainash.fields_match``.
_STANDARD_FIELDS_MATCH = frozenset({"exact", "equal", "subset", "superset", "partial"})


# ---------------------------------------------------------------------------
# Key-shape normalization (reader boundary)
# ---------------------------------------------------------------------------

def _normalize_key_fields(
    raw: Any,
    label: str,
    *,
    allow_bare_string: bool,
) -> list[str]:
    """Normalize a raw key-fields value to a validated ``list[str]``.

    Accepts a bare string only where the official Frictionless
    backward-compatibility rule permits it (``primaryKey`` and the two FK
    field locations). Lists are copied after every element is confirmed to
    be a string. Tuples, sets, mappings, scalars, invalid list elements,
    and disallowed bare strings raise ``InvalidKeyShapeError`` — no
    arbitrary iterable is coerced with ``list(...)``.
    """
    if allow_bare_string and isinstance(raw, str):
        return [raw]
    if isinstance(raw, list) and all(isinstance(value, str) for value in raw):
        return list(raw)
    raise InvalidKeyShapeError(label, raw, "list[str]")


# ---------------------------------------------------------------------------
# Field-match normalization (reader boundary)
# ---------------------------------------------------------------------------

def _normalize_fields_match(
    descriptor: Mapping[str, Any],
    spec_ext: Mapping[str, Any],
) -> str:
    """Resolve the closed six-value fields_match vocabulary from a descriptor.

    The standard property lives at ``fieldsMatch`` and carries the five
    official modes. ``open`` is a Mountainash extension carried only at
    ``x-mountainash.fields_match``. An absent standard property resolves to
    ``exact``. Invalid values, an out-of-vocabulary extension value, and
    both locations present each raise ``InvalidFieldMatchDeclaration``.
    """
    has_standard = "fieldsMatch" in descriptor
    has_extension = "fields_match" in spec_ext
    standard = descriptor.get("fieldsMatch")
    extension = spec_ext.get("fields_match")

    if has_standard and has_extension:
        raise InvalidFieldMatchDeclaration(
            standard, extension, "both standard and extension locations present"
        )
    if has_extension:
        if not isinstance(extension, str) or extension != "open":
            raise InvalidFieldMatchDeclaration(
                None, extension, "x-mountainash.fields_match must be 'open'"
            )
        return "open"
    if has_standard:
        if not isinstance(standard, str) or standard not in _STANDARD_FIELDS_MATCH:
            raise InvalidFieldMatchDeclaration(
                standard, None, "fieldsMatch is not one of the five standard modes"
            )
        return standard
    return "exact"


# ---------------------------------------------------------------------------
# Labeled-value (de)serialization for missingValues and categories
# ---------------------------------------------------------------------------

def _missing_value_to_json(mv: MissingValue) -> Any:
    if isinstance(mv, LabeledValue):
        out: Dict[str, Any] = {"value": mv.value}
        if mv.label is not None:
            out["label"] = mv.label
        return out
    return mv


def _missing_value_from_json(raw: Any) -> MissingValue:
    if isinstance(raw, dict):
        return LabeledValue(value=raw["value"], label=raw.get("label"))
    return raw


def _category_to_json(c: Any) -> Any:
    if isinstance(c, LabeledValue):
        out: Dict[str, Any] = {"value": c.value}
        if c.label is not None:
            out["label"] = c.label
        return out
    return c


def _category_from_json(raw: Any) -> Any:
    if isinstance(raw, dict):
        return LabeledValue(value=raw["value"], label=raw.get("label"))
    return raw


# ---------------------------------------------------------------------------
# Foreign key helpers
# ---------------------------------------------------------------------------

def foreign_key_from_dict(raw_fk: Mapping[str, Any]) -> ForeignKey:
    """Build a ForeignKey from a Frictionless ``foreignKeys`` entry.

    Normalizes the official v1 bare-string shorthands for ``fields`` and
    ``reference.fields``, and normalizes a self-reference marker (``""`` or
    an absent ``resource``) to ``resource=None``.
    """
    ref = raw_fk.get("reference") or {}
    raw_resource = ref.get("resource")
    resource = None if raw_resource in (None, "") else raw_resource
    return ForeignKey(
        fields=_normalize_key_fields(
            raw_fk.get("fields", []),
            "foreign_key.fields",
            allow_bare_string=True,
        ),
        reference=ForeignKeyReference(
            resource=resource,
            fields=_normalize_key_fields(
                ref.get("fields", []),
                "foreign_key.reference.fields",
                allow_bare_string=True,
            ),
        ),
    )


def foreign_key_to_dict(fk: ForeignKey) -> Dict[str, Any]:
    """Export a ForeignKey as a Frictionless ``foreignKeys`` entry.

    A ``None`` reference resource (self-reference) is omitted from the
    output entirely, per the v2 spec's optional-property omission rules.
    """
    ref: Dict[str, Any] = {"fields": list(fk.reference.fields)}
    if fk.reference.resource is not None:
        ref["resource"] = fk.reference.resource
    return {"fields": list(fk.fields), "reference": ref}


# ---------------------------------------------------------------------------
# Wire locations and descriptor-path diagnostics
# ---------------------------------------------------------------------------

_STANDARD_CONSTRAINT_KEYS = {
    "required": "required", "unique": "unique", "minimum": "minimum",
    "maximum": "maximum", "exclusive_minimum": "exclusiveMinimum",
    "exclusive_maximum": "exclusiveMaximum", "min_length": "minLength",
    "max_length": "maxLength", "pattern": "pattern", "enum": "enum",
    "json_schema": "jsonSchema",
}
# Requirements with no standard Frictionless location live under
# ``x-mountainash.constraints`` using the model's own names.
_EXTENDED_CONSTRAINT_KEYS = (
    "eq", "ne", "notin", "str_contains", "str_startswith", "str_endswith",
)
_FIELD_PROPERTY_KEYS = {
    "title": "title", "description": "description", "true_values": "trueValues",
    "false_values": "falseValues", "categories_ordered": "categoriesOrdered",
    "example": "example", "rdf_type": "rdfType", "decimal_char": "decimalChar",
    "group_char": "groupChar", "bare_number": "bareNumber", "item_type": "itemType",
    "delimiter": "delimiter",
}
_FIELD_EXTENSION_KEYS = ("rename_from", "custom_cast", "rounding", "severity")
_RETIRED_NESTED_KEYS = ("object_fields", "item_object_fields")
_UNKNOWN_DTYPE_WIRE = {"kind": "unknown"}


def _structure_error(path: str, message: str, value: Any = None) -> InvalidDescriptorStructure:
    return InvalidDescriptorStructure(
        f"{path}: {message}", descriptor_kind="schema", descriptor_path=path, rejected_value=value,
    )


def _json_path(parts: Any) -> str:
    return "$" + "".join(
        f"[{part}]" if isinstance(part, int) else f".{part}" for part in parts
    )


def _child_label(parent: str | None, name: str) -> str:
    return name if parent is None else f"{parent}.{name}"


# ---------------------------------------------------------------------------
# Values: plain JSON and field-aware lossless logical values
# ---------------------------------------------------------------------------

_VALUE_CONSTRAINTS = ("minimum", "maximum", "exclusive_minimum", "exclusive_maximum", "eq", "ne")
_SEQUENCE_CONSTRAINTS = ("enum", "notin")
_VALUE_ERRORS = (TypeError, ValueError, ArithmeticError, UnknownDtypeError)


def _json_value(value: Any) -> Any:
    """Copy the JSON value vocabulary into plain containers; reject any other Python value."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    raise ValueError(f"{type(value).__name__} has no supported JSON representation")


def _element_of(field: FieldDefinition) -> FieldDefinition | None:
    """The definition governing each collection item (a lexical list's itemType included)."""
    if isinstance(field.element, FieldDefinition):
        return field.element
    if field.type is UniversalType.LIST and field.item_type is not None:
        return FieldDefinition(type=parse_universal(field.item_type))
    return None


def _map_levels(value: Any, levels: int, convert: Callable[[Any], Any]) -> Any:
    """Apply ``convert`` to the leaves of ``levels`` nested sequences."""
    if levels == 0:
        return convert(value)
    if not isinstance(value, (list, tuple)):
        return value
    return [_map_levels(item, levels - 1, convert) for item in value]


def _levels(field: FieldDefinition) -> int:
    dimensions = field.dimensions
    return len(dimensions) if isinstance(dimensions, tuple) and dimensions else 1


def _logical_value(field: FieldDefinition, value: Any) -> Any:
    """Interpret one wire requirement value under ``field``'s declared type and format.

    Only text carrying a declared logical meaning (temporal, numeric, boolean) is
    converted; containers recurse through the declared members/element. Anything
    else is returned unchanged.
    """
    if value is None:
        return None
    kind = field.type
    if kind is UniversalType.OBJECT:
        if isinstance(value, Mapping):
            children = field.fields if isinstance(field.fields, Mapping) else {}
            return {
                key: _logical_value(children[key], item) if key in children else item
                for key, item in value.items()
            }
        return value
    if kind in (UniversalType.ARRAY, UniversalType.LIST):
        element = _element_of(field)
        if element is not None and isinstance(value, (list, tuple)):
            return _map_levels(value, _levels(field), lambda item: _logical_value(element, item))
        return value
    if not isinstance(value, str):
        return value
    if kind is UniversalType.DATETIME and field.format == "default":
        return parse_default_datetime(value)
    if kind in (UniversalType.DATE, UniversalType.TIME, UniversalType.DATETIME):
        if field.format == "any":
            return parse_temporal_any(value, kind=kind.value)
        if field.format == "default":
            return date.fromisoformat(value) if kind is UniversalType.DATE else time.fromisoformat(value)
        parsed = datetime.strptime(value, field.format)
        if kind is UniversalType.DATE:
            return parsed.date()
        return parsed.timetz() if kind is UniversalType.TIME else parsed
    if kind in (UniversalType.INTEGER, UniversalType.NUMBER):
        if field.group_char:
            value = value.replace(field.group_char, "")
        if field.decimal_char and field.decimal_char != ".":
            value = value.replace(field.decimal_char, ".")
        return Decimal(value)
    if kind is UniversalType.BOOLEAN:
        if value in (field.true_values if field.true_values is not None else ("true", "True", "TRUE", "1")):
            return True
        if value in (field.false_values if field.false_values is not None else ("false", "False", "FALSE", "0")):
            return False
    return value


def _same_value(left: Any, right: Any) -> bool:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return left.keys() == right.keys() and all(_same_value(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(_same_value(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def _wire_value(field: FieldDefinition, value: Any) -> Any:
    """Encode one typed value as JSON data that decodes to the same logical value.

    Temporal and Decimal values become their lexical text under the field's declared
    format; a value the declaration cannot restore exactly is an error, never a
    stringified or floated approximation.
    """
    if isinstance(value, (date, time, Decimal)):
        if isinstance(value, Decimal):
            text = str(value)
            if field.decimal_char and field.decimal_char != ".":
                text = text.replace(".", field.decimal_char)
        elif field.type in (UniversalType.DATE, UniversalType.TIME, UniversalType.DATETIME) and (
            field.format not in ("default", "any")
        ):
            text = value.strftime(field.format)
        else:
            text = value.isoformat()
        try:
            restored = _logical_value(field, text)
        except _VALUE_ERRORS as exc:
            raise ValueError(
                f"{value!r} cannot be represented losslessly under the declared type/format"
            ) from exc
        if type(restored) is not type(value) or restored != value:
            raise ValueError(
                f"{value!r} cannot be represented losslessly under the declared type/format"
            )
        return text
    if isinstance(value, Mapping) and field.type is UniversalType.OBJECT:
        children = field.fields if isinstance(field.fields, Mapping) else {}
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        return {
            key: _wire_value(children[key], item) if key in children else _json_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)) and field.type in (UniversalType.ARRAY, UniversalType.LIST):
        element = _element_of(field)
        if element is None:
            return _json_value(value)
        return _map_levels(value, _levels(field), lambda item: _wire_value(element, item))
    return _json_value(value)


def _with_logical_requirement_values(definition: FieldDefinition) -> FieldDefinition:
    """Decode wire requirement values to the logical values checks compare directly.

    A value its declaration cannot interpret is kept as authored; the codec adds no
    new strictness for it.
    """
    constraints = definition.constraints
    changes: Dict[str, Any] = {}
    for name in _VALUE_CONSTRAINTS:
        original = getattr(constraints, name)
        if original is None:
            continue
        try:
            logical = _logical_value(definition, original)
        except _VALUE_ERRORS:
            continue
        if not _same_value(logical, original):
            changes[name] = logical
    for name in _SEQUENCE_CONSTRAINTS:
        original = getattr(constraints, name)
        if original is None:
            continue
        try:
            logical = tuple(_logical_value(definition, item) for item in original)
        except _VALUE_ERRORS:
            continue
        if not _same_value(logical, original):
            changes[name] = logical
    if not changes:
        return definition
    return definition.variant(constraints=replace(constraints, **changes))


# ---------------------------------------------------------------------------
# Constraints helpers
# ---------------------------------------------------------------------------

def _parse_constraints(
    data: Mapping[str, Any] | None,
    enum_weights: Mapping[str, float] | None = None,
    extended: Mapping[str, Any] | None = None,
) -> FieldConstraints | None:
    """Decode standard constraints and the ``x-mountainash.constraints`` requirements."""
    if data is None and enum_weights is None and extended is None:
        return None
    properties = {
        name: data[key] for name, key in _STANDARD_CONSTRAINT_KEYS.items()
        if data is not None and key in data
    }
    properties.update({
        name: extended[name] for name in _EXTENDED_CONSTRAINT_KEYS
        if extended is not None and name in extended
    })
    return FieldConstraints(**properties, enum_weights=enum_weights)


# ---------------------------------------------------------------------------
# Dtype descriptors
# ---------------------------------------------------------------------------

_NATIVE_PERSISTENCE = "native dtype objects are in-memory-only; use a native string for persistence"


def _reject_native(dtype: Any, label: str) -> None:
    """Raise the persistence error for a native object at any depth of ``dtype``."""
    if isinstance(dtype, NativeDtype) or getattr(dtype, "native", None) is not None:
        raise InvalidDtypeDeclaration(label, _NATIVE_PERSISTENCE)
    if isinstance(dtype, (ListDtype, ArrayDtype)):
        _reject_native(dtype.element, label)
    elif isinstance(dtype, StructDtype) and dtype.fields is not SchemaTypeStatus.UNKNOWN:
        for _name, child in dtype.fields:
            _reject_native(child, label)


def _dtype_to_extension(dtype: Any) -> dict[str, Any] | None:
    """Portable leaf dtype descriptor (containers are written as fields/element)."""
    if dtype is None:
        return None
    if isinstance(dtype, NativeDtype) or getattr(dtype, "native", None) is not None:
        raise ValueError("native dtype refinements are in-memory-only")
    def known(value: Any) -> bool:
        return value is not SchemaTypeStatus.UNKNOWN
    if isinstance(dtype, MountainashDtype):
        return {"kind": "canonical", "name": dtype.value}
    if isinstance(dtype, DecimalDtype):
        return {"kind": "decimal", "precision": dtype.precision, "scale": dtype.scale}
    if dtype is SchemaTypeStatus.UNKNOWN:
        return dict(_UNKNOWN_DTYPE_WIRE)
    if isinstance(dtype, TimestampDtype):
        result = {"kind": "timestamp"}
        if known(dtype.precision):
            result["precision"] = dtype.precision
        if known(dtype.timezone_aware):
            result["timezone_aware"] = dtype.timezone_aware
        if known(dtype.timezone) or (dtype.timezone_aware is True and dtype.timezone is None):
            result["timezone"] = dtype.timezone
        return result
    if isinstance(dtype, TimeDtype):
        result = {"kind": "time"}
        if known(dtype.precision):
            result["precision"] = dtype.precision
        return result
    if isinstance(dtype, DurationDtype):
        result = {"kind": "duration"}
        if known(dtype.unit):
            result["unit"] = dtype.unit
        if known(dtype.semantics):
            result["semantics"] = dtype.semantics
        return result
    raise ValueError(f"unsupported dtype {type(dtype).__name__}")


def _dtype_from_extension(field_name: str, raw: Any) -> Any:
    if raw is None:
        return None
    def fail(reason: str, value: Any = raw):
        raise InvalidDtypeDeclaration(field_name, reason, value)
    if not isinstance(raw, Mapping):
        fail("x-mountainash.dtype must be an object")
    def decode(value: Any) -> Any:
        if not isinstance(value, Mapping):
            fail("dtype descriptor must be an object", value)
        if "native" in value:
            fail("native dtype refinements are in-memory-only", value)
        kind = value.get("kind")
        try:
            if kind == "unknown":
                return SchemaTypeStatus.UNKNOWN
            if kind == "canonical":
                return MountainashDtype(value["name"])
            if kind == "decimal":
                return DecimalDtype(value["precision"], value["scale"])
            if kind == "timestamp":
                precision = value.get("precision", SchemaTypeStatus.UNKNOWN)
                if precision is not SchemaTypeStatus.UNKNOWN and type(precision) is not int:
                    fail("timestamp precision must be an integer", value)
                aware = value.get("timezone_aware", SchemaTypeStatus.UNKNOWN)
                if aware is not SchemaTypeStatus.UNKNOWN and type(aware) is not bool:
                    fail("timezone_aware must be a boolean", value)
                return TimestampDtype(precision, aware, value.get("timezone", SchemaTypeStatus.UNKNOWN))
            if kind == "time":
                precision = value.get("precision", SchemaTypeStatus.UNKNOWN)
                if precision is not SchemaTypeStatus.UNKNOWN and type(precision) is not int:
                    fail("time precision must be an integer", value)
                return TimeDtype(precision)
            if kind == "duration":
                return DurationDtype(value.get("unit", SchemaTypeStatus.UNKNOWN), value.get("semantics", SchemaTypeStatus.UNKNOWN))
            if kind in {"list", "array"}:
                child = decode(value.get("element", {"kind": "unknown"}))
                if kind == "list":
                    return ListDtype(child)
                dimensions = value.get("dimensions", SchemaTypeStatus.UNKNOWN)
                if dimensions is not SchemaTypeStatus.UNKNOWN:
                    if not isinstance(dimensions, list) or not dimensions or any(type(d) is not int or d < 0 for d in dimensions):
                        fail("array dimensions must be non-negative integers", value)
                    dimensions = tuple(dimensions)
                return ArrayDtype(child, dimensions)
            if kind == "struct":
                children = value.get("fields", SchemaTypeStatus.UNKNOWN)
                if children is SchemaTypeStatus.UNKNOWN:
                    return StructDtype(children)
                if not isinstance(children, list):
                    fail("struct fields must be a list", value)
                names, result = set(), []
                for child in children:
                    if not isinstance(child, Mapping) or not isinstance(child.get("name"), str):
                        fail("struct child requires a name", child)
                    if child["name"] in names:
                        fail("duplicate struct child", child)
                    names.add(child["name"])
                    result.append((child["name"], decode(child.get("dtype", {"kind": "unknown"}))))
                return StructDtype(tuple(result))
        except InvalidDtypeDeclaration:
            raise
        except (KeyError, TypeError, ValueError, UnknownDtypeError) as exc:
            raise InvalidDtypeDeclaration(field_name, str(exc), value) from exc
        fail(f"unknown dtype kind {kind!r}", value)
    return decode(raw)


def _dtype_to_definition_kwargs(dtype: Any) -> Dict[str, Any]:
    """Normalize a bare dtype tree into definition composition kwargs.

    Struct children / list or array element become ``fields`` / ``element``
    (known definitions or UNKNOWN); scalars stay type-only ``dtype``. The
    definition derives its own dtype from the composition.
    """
    if isinstance(dtype, StructDtype):
        if dtype.fields is SchemaTypeStatus.UNKNOWN:
            return {"fields": SchemaTypeStatus.UNKNOWN}
        return {"fields": {
            name: FieldDefinition(**_dtype_to_definition_kwargs(child))
            for name, child in dtype.fields
        }}
    if isinstance(dtype, (ListDtype, ArrayDtype)):
        element = (
            SchemaTypeStatus.UNKNOWN
            if dtype.element is SchemaTypeStatus.UNKNOWN
            else FieldDefinition(**_dtype_to_definition_kwargs(dtype.element))
        )
        kwargs: Dict[str, Any] = {"element": element}
        if isinstance(dtype, ArrayDtype):
            kwargs["dimensions"] = dtype.dimensions
        return kwargs
    return {"dtype": dtype}


# ---------------------------------------------------------------------------
# Export: one recursive body writer for named fields and unnamed elements
# ---------------------------------------------------------------------------

def _shape_to_wire(definition: FieldDefinition, path: str, label: str) -> dict[str, Any]:
    """Write the single structural authority: ``fields``, ``element``/``dimensions`` or leaf ``dtype``.

    Known bare struct/list/array dtypes are normalized to the same composition a
    declared ``fields``/``element`` produces. Unknown struct shape, empty fields,
    unknown element and unknown or fixed dimensions stay distinct.
    """
    unknown = SchemaTypeStatus.UNKNOWN
    fields, element, dimensions = definition.fields, definition.element, definition.dimensions
    if fields is None and element is None and dimensions is None:
        dtype = definition.dtype
        if dtype is None:
            return {}
        _reject_native(dtype, label)
        composition = _dtype_to_definition_kwargs(dtype)
        if "dtype" in composition:
            try:
                return {"dtype": _dtype_to_extension(dtype)}
            except (TypeError, ValueError) as exc:
                raise InvalidDtypeDeclaration(label, str(exc)) from exc
        fields = composition.get("fields")
        element = composition.get("element")
        dimensions = composition.get("dimensions")
    if fields is unknown:
        return {"dtype": {"kind": "struct"}}
    extension: Dict[str, Any] = {}
    if isinstance(fields, Mapping):
        extension["fields"] = [
            _field_to_frictionless_dict(
                child, child_name,
                path=f"{path}.x-mountainash.fields[{index}]", label=_child_label(label, child_name),
            )
            for index, (child_name, child) in enumerate(fields.items())
        ]
        return extension
    if isinstance(element, FieldDefinition):
        extension["element"] = _field_to_frictionless_dict(
            element, None, path=f"{path}.x-mountainash.element", label=f"{label}.<element>",
        )
    else:
        extension["element"] = {"x-mountainash": {"dtype": dict(_UNKNOWN_DTYPE_WIRE)}}
    if dimensions is unknown:
        extension["dimensions"] = dict(_UNKNOWN_DTYPE_WIRE)
    elif dimensions is not None:
        extension["dimensions"] = list(dimensions)
    return extension


def _field_to_frictionless_dict(
    definition: FieldDefinition, name: str | None = None, *, path: str = "$", label: str | None = None,
) -> Dict[str, Any]:
    """Export one definition to a Frictionless field body.

    ``name`` is the local name supplied by the enclosing field mapping; an unnamed
    collection element passes ``None`` and gets no ``name`` key. Nested
    ``fields`` / ``element`` recurse through this same function. The ``type`` key
    is omitted exactly when the type is ``ANY``. Values are copied into plain JSON
    containers; unrepresentable values raise ``InvalidDescriptorStructure`` at
    their property path.
    """
    if label is None:
        label = name if name is not None else "<element>"

    def encode(location: str, encoder: Callable[[Any], Any], value: Any) -> Any:
        try:
            return encoder(value)
        except (TypeError, ValueError) as exc:
            raise _structure_error(location, str(exc)) from exc

    def typed(value: Any) -> Any:
        return _wire_value(definition, value)

    def typed_items(items: Any) -> list:
        return [_wire_value(definition, item) for item in items]

    body: Dict[str, Any] = {} if name is None else {"name": name}
    if definition.type is not UniversalType.ANY:
        body["type"] = definition.type.value
    if definition.format != "default":
        body["format"] = definition.format
    for attribute, key in _FIELD_PROPERTY_KEYS.items():
        value = getattr(definition, attribute)
        if value is not None:
            body[key] = encode(f"{path}.{key}", _json_value, value)
    if definition.missing_values is not None:
        body["missingValues"] = encode(
            f"{path}.missingValues", _json_value,
            [_missing_value_to_json(mv) for mv in definition.missing_values],
        )
    if definition.categories is not None:
        body["categories"] = encode(
            f"{path}.categories", _json_value,
            [_category_to_json(c) for c in definition.categories],
        )

    extension: Dict[str, Any] = {}
    constraints = definition.constraints
    standard: Dict[str, Any] = {}
    for attribute, key in _STANDARD_CONSTRAINT_KEYS.items():
        value = getattr(constraints, attribute)
        if value is None or (attribute in ("required", "unique") and value is False):
            continue
        location = f"{path}.constraints.{key}"
        if attribute in _VALUE_CONSTRAINTS:
            standard[key] = encode(location, typed, value)
        elif attribute in _SEQUENCE_CONSTRAINTS:
            standard[key] = encode(location, typed_items, value)
        else:
            standard[key] = encode(location, _json_value, value)
    if standard:
        body["constraints"] = standard
    extended: Dict[str, Any] = {}
    for attribute in _EXTENDED_CONSTRAINT_KEYS:
        value = getattr(constraints, attribute)
        if value is None:
            continue
        location = f"{path}.x-mountainash.constraints.{attribute}"
        if attribute in _VALUE_CONSTRAINTS:
            extended[attribute] = encode(location, typed, value)
        elif attribute in _SEQUENCE_CONSTRAINTS:
            extended[attribute] = encode(location, typed_items, value)
        else:
            extended[attribute] = value
    if extended:
        extension["constraints"] = extended
    if constraints.enum_weights is not None:
        extension["enum_weights"] = encode(
            f"{path}.x-mountainash.enum_weights", _json_value, constraints.enum_weights,
        )
    for key in _FIELD_EXTENSION_KEYS:
        value = getattr(definition, key)
        if value is not None:
            extension[key] = value
    if definition.null_fill is not None:
        extension["null_fill"] = encode(f"{path}.x-mountainash.null_fill", typed, definition.null_fill)
    if definition.backend_type is not None:
        if isinstance(definition.backend_type, NativeDtype):
            raise InvalidDtypeDeclaration(label, _NATIVE_PERSISTENCE)
        extension["backend_type"] = definition.backend_type
    extension.update(_shape_to_wire(definition, path, label))
    if extension:
        body["x-mountainash"] = extension
    return body


def table_schema_to_frictionless(schema: TableSchema) -> Dict[str, Any]:
    """Convert a TableSchema to a Frictionless Table Schema descriptor dict.

    Standard Frictionless properties are placed at their canonical locations.
    Mountainash extensions are stored under ``x-mountainash`` keys, added only
    when there are actual extensions to store. Local field names come from the
    ``schema.fields`` mapping keys.
    """
    reject_typed_profile_at(
        schema.schema_url,
        descriptor_kind="schema",
        extras=None,
        location=InvariantLocation("$"),
    )
    descriptor: Dict[str, Any] = {}

    if schema.title:
        descriptor["title"] = schema.title
    if schema.description:
        descriptor["description"] = schema.description
    if schema.primary_key is not None:
        descriptor["primaryKey"] = list(schema.primary_key)
    # fields_match: exact is the default and omitted; the four other standard
    # modes go to the standard key; ``open`` moves to x-mountainash below.
    if schema.fields_match not in ("exact", "open"):
        descriptor["fieldsMatch"] = schema.fields_match
    if schema.unique_keys is not None:
        descriptor["uniqueKeys"] = [list(key) for key in schema.unique_keys]
    if schema.schema_url is not None:
        descriptor["$schema"] = schema.schema_url

    if schema.foreign_keys:
        descriptor["foreignKeys"] = [foreign_key_to_dict(fk) for fk in schema.foreign_keys]

    # Schema-level None and [] both disable sentinels; encode either explicitly
    # so decoding cannot restore the omitted-property default [""].
    if schema.missing_values is None or list(schema.missing_values) != [""]:
        descriptor["missingValues"] = [
            _missing_value_to_json(mv) for mv in (schema.missing_values or ())
        ]

    # "open" is a mountainash-only fields_match value serialized only here;
    # contract is mountainash-only outright.
    schema_ext: Dict[str, Any] = {}
    if schema.fields_match == "open":
        schema_ext["fields_match"] = "open"
    if schema.contract:
        schema_ext["contract"] = dict(schema.contract)
    if schema_ext:
        descriptor["x-mountainash"] = schema_ext

    descriptor["fields"] = [
        _field_to_frictionless_dict(definition, name, path=f"$.fields[{index}]")
        for index, (name, definition) in enumerate(schema.fields.items())
    ]
    return descriptor


# ---------------------------------------------------------------------------
# Import: local recursive Draft-07 grammar, then one recursive body decoder
# ---------------------------------------------------------------------------

@cache
def _declaration_validator() -> Any:
    """The bundled grammar: no download, profile registry or remote reference."""
    grammar = json.loads(
        files("mountainash.typespec").joinpath("schemas/field-declarations.json").read_text(encoding="utf-8")
    )
    # Resolved descriptors may be any Mapping (e.g. a read-only view), not only dict.
    checker = Draft7Validator.TYPE_CHECKER.redefine(
        "object", lambda _checker, instance: isinstance(instance, Mapping),
    )
    return extend(Draft7Validator, type_checker=checker)(grammar)


def _validate_declarations(descriptor: Mapping[str, Any]) -> None:
    """Check required root fields, recursive shapes and container combinations."""
    errors = list(_declaration_validator().iter_errors(descriptor))
    if not errors:
        return
    error = min(errors, key=lambda e: (len(e.absolute_path), [str(p) for p in e.absolute_path], e.message))
    raise _structure_error(_json_path(error.absolute_path), error.message, error.instance)


def _members_from_wire(raw_members: list, path: str, parent_label: str | None) -> Dict[str, FieldDefinition]:
    """Decode ordered named members, rejecting duplicate siblings before any mapping exists."""
    seen: set[str] = set()
    for index, raw_member in enumerate(raw_members):
        name = raw_member["name"]
        if name in seen:
            raise _structure_error(f"{path}[{index}].name", f"duplicate field name {name!r}", name)
        seen.add(name)
    return {
        raw_member["name"]: _field_from_frictionless_dict(
            raw_member, path=f"{path}[{index}]", label=_child_label(parent_label, raw_member["name"]),
        )
        for index, raw_member in enumerate(raw_members)
    }


def _field_from_frictionless_dict(
    raw_field: Mapping[str, Any], *, path: str = "$", label: str | None = None,
) -> FieldDefinition:
    """Decode one body. Names belong to the containing mapping, never the definition.

    An absent ``type`` defaults to ``any``; a leading ``fmt:`` prefix on the
    format is normalized off at this boundary. Retired ``object_fields`` /
    ``item_object_fields`` are rejected, never interpreted. The grammar has
    already established container shapes and name presence.
    """
    if label is None:
        label = raw_field.get("name", "<element>")
    extension: Mapping[str, Any] = raw_field.get("x-mountainash", {})
    for retired in _RETIRED_NESTED_KEYS:
        if retired in extension:
            raise _structure_error(
                f"{path}.x-mountainash.{retired}",
                "retired nested declaration; call migrate_nested_field_declarations() "
                "explicitly and read the migrated descriptor",
                extension[retired],
            )

    properties: Dict[str, Any] = {
        attribute: raw_field[key] for attribute, key in _FIELD_PROPERTY_KEYS.items() if key in raw_field
    }
    properties.update({
        key: extension[key] for key in (*_FIELD_EXTENSION_KEYS, "backend_type", "null_fill")
        if key in extension
    })
    properties["type"] = parse_universal(raw_field.get("type", "any"))
    properties["format"] = raw_field.get("format", "default").removeprefix("fmt:")
    properties["constraints"] = _parse_constraints(
        raw_field.get("constraints"), extension.get("enum_weights"), extension.get("constraints"),
    )
    if "missingValues" in raw_field:
        properties["missing_values"] = [_missing_value_from_json(mv) for mv in raw_field["missingValues"]]
    if "categories" in raw_field:
        properties["categories"] = [_category_from_json(c) for c in raw_field["categories"]]

    if "fields" in extension:
        properties["fields"] = _members_from_wire(
            extension["fields"], f"{path}.x-mountainash.fields", label,
        )
    if "element" in extension:
        properties["element"] = _field_from_frictionless_dict(
            extension["element"], path=f"{path}.x-mountainash.element", label=f"{label}.<element>",
        )
    if "dimensions" in extension:
        dimensions = extension["dimensions"]
        properties["dimensions"] = (
            SchemaTypeStatus.UNKNOWN if isinstance(dimensions, Mapping) else tuple(dimensions)
        )
    if "dtype" in extension:
        properties.update(_dtype_to_definition_kwargs(_dtype_from_extension(label, extension["dtype"])))

    try:
        definition = FieldDefinition(**properties)
    except InvalidDtypeDeclaration as exc:
        if exc.field_name is not None:
            raise
        raise InvalidDtypeDeclaration(label, exc.reason, exc.rejected_value) from exc
    return _with_logical_requirement_values(definition)


def table_schema_from_frictionless(data: Mapping[str, Any]) -> TableSchema:
    """Create a TableSchema from a resolved Frictionless Table Schema mapping.

    The v2 descriptor codec resolves JSON text and path references before
    calling this adapter. Direct callers must provide a schema mapping.

    Notes:
        - The root must carry ``fields``; malformed declarations raise
          ``InvalidDescriptorStructure`` with the property path.
        - Missing field types default to ``any``.
        - Omitted schema-level ``missingValues`` defaults to ``[""]``.
        - Unrelated custom properties keep their existing treatment (ignored).
        - Retired nested keys are rejected with migration guidance; the reader
          never migrates.
    """
    if not isinstance(data, Mapping):
        raise TypeError("table_schema_from_frictionless() requires a resolved schema mapping")

    descriptor = data
    _validate_declarations(descriptor)
    raw_primary_key = descriptor.get("primaryKey")
    primary_key = (
        None
        if raw_primary_key is None
        else _normalize_key_fields(raw_primary_key, "primary_key", allow_bare_string=True)
    )

    raw_unique_keys = descriptor.get("uniqueKeys")
    if raw_unique_keys is not None and not isinstance(raw_unique_keys, list):
        raise InvalidKeyShapeError("unique_keys", raw_unique_keys, "list[list[str]]")
    unique_keys: Optional[List[List[str]]] = (
        None
        if raw_unique_keys is None
        else [
            _normalize_key_fields(raw_key, f"unique_keys[{index}]", allow_bare_string=False)
            for index, raw_key in enumerate(raw_unique_keys)
        ]
    )

    missing_values: List[MissingValue] = (
        [_missing_value_from_json(mv) for mv in descriptor["missingValues"]]
        if "missingValues" in descriptor
        else [""]
    )

    # ``fields_match: "open"`` is the mountainash-only extension form;
    # ``contract`` is validated eagerly so a malformed descriptor fails fast.
    schema_ext: Dict[str, Any] = descriptor.get("x-mountainash", {}) or {}
    fields_match: str = _normalize_fields_match(descriptor, schema_ext)
    contract: Optional[Dict[str, str]] = schema_ext.get("contract") or None
    if contract is not None:
        validate_contract_dict(contract)
    foreign_keys: Optional[List[ForeignKey]] = (
        list(parse_foreign_keys_at(descriptor, location=InvariantLocation("$")))
        if "foreignKeys" in descriptor
        else None
    )

    return TableSchema(
        fields=_members_from_wire(descriptor["fields"], "$.fields", None),
        title=descriptor.get("title"),
        description=descriptor.get("description"),
        primary_key=primary_key,
        foreign_keys=foreign_keys,
        missing_values=missing_values,
        fields_match=fields_match,
        unique_keys=unique_keys,
        schema_url=descriptor.get("$schema"),
        contract=contract,
    )


# ---------------------------------------------------------------------------
# Explicit pure legacy migration
# ---------------------------------------------------------------------------
#
# The only place retired ``object_fields`` / ``item_object_fields`` are
# interpreted. It edits copied descriptor data; untouched raw content (custom
# properties, metadata) is carried over as-is and never round-tripped through
# the typed codec. Precedence follows the approved migration rules: a native
# override stays on the declaration independently; otherwise the canonical
# parent shape, order and known child types win, compatible legacy declarations
# fill unknown parameters (existing ``resolve_dtype_parameters``), and metadata
# whose name matches a canonical member stays attached to it. No conflict
# rejection.

def _migration_members(raw: Any, path: str) -> Dict[str, dict]:
    if not isinstance(raw, list):
        raise _structure_error(path, "fields must be a list", raw)
    members: Dict[str, dict] = {}
    for index, child in enumerate(raw):
        location = f"{path}[{index}]"
        if not isinstance(child, Mapping) or not isinstance(child.get("name"), str):
            raise _structure_error(location, "a named field is required", child)
        name = child["name"]
        if name in members:
            raise _structure_error(f"{location}.name", f"duplicate field name {name!r}", name)
        members[name] = _migrate_field_body(child, location)
    return members


def _migration_dtype(raw: Mapping[str, Any], label: str) -> Any:
    """Portable type intent of a raw body; native overrides and metadata stay separate."""
    from .converters import _resolve_broad_field_canonical

    extension = raw.get("x-mountainash") or {}
    if "dtype" in extension:
        return _dtype_from_extension(label, extension["dtype"])
    if "fields" in extension:
        return StructDtype(tuple(
            (child["name"], _migration_dtype(child, label) or SchemaTypeStatus.UNKNOWN)
            for child in extension["fields"]
        ))
    if "element" in extension:
        element = _migration_dtype(extension["element"], label) or SchemaTypeStatus.UNKNOWN
        dimensions = extension.get("dimensions")
        if dimensions is None:
            return ListDtype(element)
        return ArrayDtype(
            element, SchemaTypeStatus.UNKNOWN if isinstance(dimensions, Mapping) else tuple(dimensions),
        )
    return _resolve_broad_field_canonical(FieldDefinition(
        type=parse_universal(raw.get("type", "any")),
        format=raw.get("format", "default").removeprefix("fmt:"),
    ))


def _migrate_field_body(
    raw: Mapping[str, Any], path: str, *, parent_dtype: Any = None,
) -> Dict[str, Any]:
    """Migrate one owned body. ``parent_dtype`` is the canonical type its parent assigns it."""
    if not isinstance(raw, Mapping):
        raise _structure_error(path, "a field declaration must be an object", raw)
    result = dict(raw)  # bodies are owned: the public entry point deep-copies once
    extension = dict(result.get("x-mountainash") or {})
    if "x-mountainash" in result:
        result["x-mountainash"] = extension
    has_legacy = any(key in extension for key in _RETIRED_NESTED_KEYS)

    members: Dict[str, dict] | None = None
    if "fields" in extension:
        members = _migration_members(extension["fields"], f"{path}.x-mountainash.fields")
        extension["fields"] = list(members.values())
    if "element" in extension:
        extension["element"] = _migrate_field_body(extension["element"], f"{path}.x-mountainash.element")
    if not has_legacy and parent_dtype is None:
        return result

    declared = _migration_dtype(result, path)
    selected = declared
    if parent_dtype is not None:
        selected = (
            declared if parent_dtype is SchemaTypeStatus.UNKNOWN and declared is not None
            else resolve_dtype_parameters(parent_dtype, declared)
        )

    legacy_members: Dict[str, dict] = {}
    old_fields = extension.pop("object_fields", None)
    old_items = extension.pop("item_object_fields", None)
    if old_fields is not None:
        legacy_members = _migration_members(old_fields, f"{path}.x-mountainash.object_fields")
        evidence = StructDtype(tuple(
            (name, _migration_dtype(child, path) or SchemaTypeStatus.UNKNOWN)
            for name, child in legacy_members.items()
        ))
        if selected is None or selected is SchemaTypeStatus.UNKNOWN or selected is MountainashDtype.STRUCT:
            selected = evidence
        elif isinstance(selected, StructDtype):
            selected = resolve_dtype_parameters(selected, evidence)
    element_body = extension.get("element")
    if old_items is not None:
        item_members = _migration_members(old_items, f"{path}.x-mountainash.item_object_fields")
        legacy_element = {"type": "object", "x-mountainash": {"fields": list(item_members.values())}}
        evidence = ListDtype(_migration_dtype(legacy_element, path))
        if element_body is None:
            element_body = legacy_element
        if selected is None or selected is SchemaTypeStatus.UNKNOWN or selected is MountainashDtype.LIST:
            selected = evidence
        elif isinstance(selected, (ListDtype, ArrayDtype)):
            selected = resolve_dtype_parameters(selected, evidence)

    # Canonical type/order wins, while metadata and unrelated custom properties
    # remain on their original named declaration.
    portable = _field_to_frictionless_dict(FieldDefinition(dtype=selected), None, path=path)
    for key in ("type", "format"):
        if key in portable:
            result[key] = portable[key]
    for key in ("dtype", "fields", "element", "dimensions"):
        extension.pop(key, None)
    extension.update(portable.get("x-mountainash", {}))
    if isinstance(selected, StructDtype) and selected.fields is not SchemaTypeStatus.UNKNOWN:
        candidates = {**legacy_members, **(members or {})}
        extension["fields"] = [
            _migrate_field_body(
                candidates.get(name, {"name": name}), f"{path}.x-mountainash.fields[{index}]",
                parent_dtype=dtype,
            )
            for index, (name, dtype) in enumerate(selected.fields)
        ]
    elif isinstance(selected, (ListDtype, ArrayDtype)):
        extension["element"] = _migrate_field_body(
            element_body or {}, f"{path}.x-mountainash.element", parent_dtype=selected.element,
        )
    if extension:
        result["x-mountainash"] = extension
    else:
        result.pop("x-mountainash", None)
    return result


def migrate_nested_field_declarations(schema_descriptor: Mapping[str, Any]) -> dict:
    """Return a fresh descriptor with retired nested declarations explicitly migrated.

    Replaces ``x-mountainash.object_fields`` / ``item_object_fields`` with
    ``fields`` / ``element`` recursively. Native string overrides stay on their
    declaration; the portable parent shape, order and known child types win;
    compatible legacy declarations supply unknown parameters; matching metadata
    stays attached by name. Descriptors already in the current form are returned
    as an equal, independently owned copy. The input is never mutated and no
    files, references, packages or backends are involved.
    """
    if not isinstance(schema_descriptor, Mapping):
        raise TypeError("migrate_nested_field_declarations() requires a schema mapping")
    migrated = deepcopy(dict(schema_descriptor))
    if "fields" in migrated:
        migrated["fields"] = list(_migration_members(migrated["fields"], "$.fields").values())
    return migrated


class FrictionlessSchemaCodec(SchemaCodec[Mapping[str, Any]]):
    """SchemaCodec for resolved Frictionless Table Schema mappings.

    Pure import/export over the module functions above; performs no file,
    network or reference resolution.
    """

    def decode(self, descriptor: Mapping[str, Any]) -> TableSchema:
        return table_schema_from_frictionless(descriptor)

    def encode(self, schema: TableSchema) -> Dict[str, Any]:
        return table_schema_to_frictionless(schema)


__all__ = [
    "FrictionlessSchemaCodec",
    "table_schema_to_frictionless",
    "table_schema_from_frictionless",
    "migrate_nested_field_declarations",
    "foreign_key_from_dict",
    "foreign_key_to_dict",
]
