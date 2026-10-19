"""
Frictionless Table Schema import/export for TypeSpec.

Provides two public functions:
- typespec_to_frictionless(spec) → dict
- typespec_from_frictionless(data) → TypeSpec

Mountainash-specific extensions (rename_from, null_fill)
are stored under the ``x-mountainash`` namespace key, following the
Frictionless custom extension convention.

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from functools import cache
from importlib.resources import files
import json

from jsonschema import Draft7Validator
from jsonschema.validators import extend
from typing import Any, Dict, List, Optional

from mountainash.conform.contract import validate_contract_dict

from mountainash.core.dtypes import (
    ArrayDtype, DecimalDtype, DurationDtype, ListDtype, MountainashDtype,
    NativeDtype, SchemaTypeStatus, StructDtype, TimeDtype, TimestampDtype,
)
from mountainash.core.dtypes.errors import UnknownDtypeError

from .errors import (
    InvalidDescriptorStructure, InvalidDtypeDeclaration, InvalidFieldMatchDeclaration,
    InvalidKeyShapeError, TypeSpecError,
)
from ._field_values import (
    _SEQUENCE_CONSTRAINTS, _VALUE_CONSTRAINTS, field_value_to_json, json_value,
)
from .frictionless_invariants import (
    InvariantLocation,
    parse_foreign_keys_at,
    reject_typed_profile_at,
)
from .spec import (
    FieldConstraints,
    FieldSpec,
    ForeignKey,
    ForeignKeyReference,
    LabeledValue,
    MissingValue,
    TypeSpec,
)
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
# Constraints helpers
# ---------------------------------------------------------------------------

_STANDARD_CONSTRAINT_KEYS = {
    "required": "required", "unique": "unique", "minimum": "minimum",
    "maximum": "maximum", "exclusive_minimum": "exclusiveMinimum",
    "exclusive_maximum": "exclusiveMaximum", "min_length": "minLength",
    "max_length": "maxLength", "pattern": "pattern", "enum": "enum",
    "json_schema": "jsonSchema",
}
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


def _constraint_value(field: FieldSpec | None, name: str, value: Any) -> Any:
    if field is not None:
        if name in _VALUE_CONSTRAINTS:
            return field_value_to_json(field, value)
        if name in _SEQUENCE_CONSTRAINTS:
            return [field_value_to_json(field, item) for item in value]
    return json_value(value)


def _constraints_to_dict(
    constraints: FieldConstraints, *, field: FieldSpec | None = None,
) -> dict:
    result = {}
    for name, key in _STANDARD_CONSTRAINT_KEYS.items():
        value = getattr(constraints, name)
        if value is None or (name in ("required", "unique") and value is False):
            continue
        result[key] = _constraint_value(field, name, value)
    return result


def _parse_constraints(
    data: Mapping[str, Any] | None,
    enum_weights: Mapping[str, float] | None = None,
    extended: Mapping[str, Any] | None = None,
) -> FieldConstraints | None:
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
# Export: TypeSpec → Frictionless dict
# ---------------------------------------------------------------------------

def _dtype_to_extension(dtype: Any) -> dict[str, Any] | None:
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
        return {"kind": "unknown"}
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
    if isinstance(dtype, (ListDtype, ArrayDtype)):
        result = {"kind": "array" if isinstance(dtype, ArrayDtype) else "list"}
        child = _dtype_to_extension(dtype.element)
        if child is not None:
            result["element"] = child
        if isinstance(dtype, ArrayDtype) and known(dtype.dimensions):
            result["dimensions"] = list(dtype.dimensions)
        return result
    if isinstance(dtype, StructDtype):
        result = {"kind": "struct"}
        if known(dtype.fields):
            result["fields"] = [{"name": name, "dtype": _dtype_to_extension(child)}
                                for name, child in dtype.fields]
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


def _field_to_frictionless_dict(
    fspec: FieldSpec, *, name: str | None = None, path: str = "$",
) -> dict[str, Any]:
    """Encode the shared body, adding a contextual name only for named uses."""
    from .converters import declared_element, declared_fields

    result = {} if name is None else {"name": name}
    if fspec.type is not UniversalType.ANY:
        result["type"] = fspec.type.value
    if fspec.format != "default":
        result["format"] = fspec.format
    extension = {}
    try:
        for property_name, wire_name in _FIELD_PROPERTY_KEYS.items():
            value = getattr(fspec, property_name)
            if value is not None:
                result[wire_name] = json_value(value)
        if fspec.missing_values is not None:
            result["missingValues"] = json_value([
                _missing_value_to_json(value) for value in fspec.missing_values
            ])
        if fspec.categories is not None:
            result["categories"] = json_value([_category_to_json(value) for value in fspec.categories])
        if fspec.constraints is not None:
            constraints = _constraints_to_dict(fspec.constraints, field=fspec)
            if constraints:
                result["constraints"] = constraints
            extended = {
                key: _constraint_value(fspec, key, getattr(fspec.constraints, key))
                for key in _EXTENDED_CONSTRAINT_KEYS
                if getattr(fspec.constraints, key) is not None
            }
            if extended:
                extension["constraints"] = extended
            if fspec.constraints.enum_weights is not None:
                extension["enum_weights"] = json_value(fspec.constraints.enum_weights)
        for key in _FIELD_EXTENSION_KEYS:
            value = getattr(fspec, key)
            if value is not None:
                extension[key] = json_value(value)
        if fspec.null_fill is not None:
            extension["null_fill"] = field_value_to_json(fspec, fspec.null_fill)
    except (TypeError, ValueError) as exc:
        raise InvalidDescriptorStructure(
            f"{path}: {exc}", descriptor_kind="schema", descriptor_path=path,
        ) from exc
    if fspec.backend_type is not None:
        if isinstance(fspec.backend_type, NativeDtype):
            raise InvalidDtypeDeclaration(
                path, "native dtype objects are in-memory-only; use a native string for persistence",
            )
        extension["backend_type"] = fspec.backend_type
    dtype = fspec.dtype
    if isinstance(dtype, NativeDtype) or getattr(dtype, "native", None) is not None:
        raise InvalidDtypeDeclaration(path, "native dtype refinements are in-memory-only")
    if fspec.fields is not None or (
        isinstance(dtype, StructDtype) and dtype.fields is not SchemaTypeStatus.UNKNOWN
    ):
        extension["fields"] = [
            _field_to_frictionless_dict(child, name=child_name, path=f"{path}.x-mountainash.fields[{index}]")
            for index, (child_name, child) in enumerate(declared_fields(fspec).items())
        ]
    elif fspec.element is not None or isinstance(dtype, (ListDtype, ArrayDtype)):
        extension["element"] = _field_to_frictionless_dict(
            declared_element(fspec), path=f"{path}.x-mountainash.element",
        )
        dimensions = fspec.dimensions if fspec.element is not None else getattr(dtype, "dimensions", None)
        if dimensions is not None:
            extension["dimensions"] = (
                {"kind": "unknown"} if dimensions is SchemaTypeStatus.UNKNOWN else list(dimensions)
            )
    elif dtype is not None:
        try:
            extension["dtype"] = _dtype_to_extension(dtype)
        except (TypeError, ValueError) as exc:
            raise InvalidDtypeDeclaration(path, str(exc)) from exc
    if extension:
        result["x-mountainash"] = extension
    return result


def typespec_to_frictionless(spec: TypeSpec) -> Dict[str, Any]:
    """Convert a TypeSpec to a Frictionless Table Schema descriptor dict.

    Standard Frictionless fields are placed at their canonical locations.
    Mountainash extensions (rename_from, null_fill per-field) are stored
    under ``x-mountainash`` keys — added only when there are actual
    extensions to store.

    Args:
        spec: The TypeSpec to export.

    Returns:
        A Frictionless Table Schema descriptor dict.
    """
    reject_typed_profile_at(
        spec.schema_url,
        descriptor_kind="schema",
        extras=None,
        location=InvariantLocation("$"),
    )
    descriptor: Dict[str, Any] = {}

    if spec.title:
        descriptor["title"] = spec.title
    if spec.description:
        descriptor["description"] = spec.description
    if spec.primary_key is not None:
        # Always a list — the model type guarantees this; no special-casing.
        descriptor["primaryKey"] = spec.primary_key
    # fields_match: exact is the default and omitted; the four other standard
    # modes go to the standard key; ``open`` moves to x-mountainash below.
    if spec.fields_match not in ("exact", "open"):
        descriptor["fieldsMatch"] = spec.fields_match
    if spec.unique_keys is not None:  # Gap 4
        descriptor["uniqueKeys"] = spec.unique_keys
    if spec.schema_url is not None:
        descriptor["$schema"] = spec.schema_url

    # Foreign keys (standard Frictionless field)
    if spec.foreign_keys:
        fk_list = [foreign_key_to_dict(fk) for fk in spec.foreign_keys]
        descriptor["foreignKeys"] = fk_list

    # Gap 1: missingValues (schema-level) — emit if non-default. The default
    # [""] is omitted; an explicit [] is emitted (disables sentinel handling).
    if spec.missing_values is not None and spec.missing_values != [""]:
        descriptor["missingValues"] = [
            _missing_value_to_json(mv) for mv in spec.missing_values
        ]

    # Spec-level x-mountainash extensions: "open" is a mountainash-only
    # fields_match value serialized only here; contract (item 48) is
    # mountainash-only outright.
    spec_ext: Dict[str, Any] = {}
    if spec.fields_match == "open":
        spec_ext["fields_match"] = "open"
    if spec.contract:
        spec_ext["contract"] = dict(spec.contract)
    if spec_ext:
        descriptor["x-mountainash"] = spec_ext

    # Fields
    fields_list = [
        _field_to_frictionless_dict(fspec, name=name, path=f"$.fields[{index}]")
        for index, (name, fspec) in enumerate(spec.fields.items())
    ]

    descriptor["fields"] = fields_list
    return json_value(descriptor)


# Import: resolved Frictionless schema mapping → TypeSpec
# ---------------------------------------------------------------------------

@cache
def _declaration_validator():
    schema = json.loads(files("mountainash.typespec").joinpath("schemas/field-declarations.json").read_text())
    object_types = Draft7Validator.TYPE_CHECKER.redefine(
        "object", lambda checker, instance: isinstance(instance, Mapping),
    )
    return extend(Draft7Validator, type_checker=object_types)(schema)


def _validate_declaration_descriptor(descriptor: Mapping[str, Any]) -> None:
    error = next(_declaration_validator().iter_errors(descriptor), None)
    if error is not None:
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        raise InvalidDescriptorStructure(
            f"{path}: {error.message}", descriptor_kind="schema",
            descriptor_path=path, rejected_value=error.instance,
        )


def _fields_from_frictionless(raw_fields: list, path: str) -> dict[str, FieldSpec]:
    result = {}
    for index, raw_field in enumerate(raw_fields):
        name = raw_field["name"]
        field_path = f"{path}[{index}]"
        if name in result:
            raise InvalidDescriptorStructure(
                f"{field_path}.name: duplicate field name {name!r}",
                descriptor_kind="schema", descriptor_path=f"{field_path}.name",
                rejected_value=name,
            )
        result[name] = _field_from_frictionless_dict(raw_field, path=field_path)
    return result


def _field_from_frictionless_dict(
    raw_field: Mapping[str, Any], *, path: str = "$",
) -> FieldSpec:
    """Decode one body; names belong to its containing mapping, never its definition."""
    extension = raw_field.get("x-mountainash", {})
    for key in ("object_fields", "item_object_fields"):
        if key in extension:
            location = f"{path}.x-mountainash.{key}"
            raise InvalidDescriptorStructure(
                f"{location}: retired property; call migrate_nested_field_declarations() explicitly",
                descriptor_kind="schema", descriptor_path=location,
            )
    properties = {
        name: raw_field[key] for name, key in _FIELD_PROPERTY_KEYS.items() if key in raw_field
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
        properties["missing_values"] = [_missing_value_from_json(value) for value in raw_field["missingValues"]]
    if "categories" in raw_field:
        properties["categories"] = [_category_from_json(value) for value in raw_field["categories"]]
    if "fields" in extension:
        properties["fields"] = _fields_from_frictionless(
            extension["fields"], f"{path}.x-mountainash.fields",
        )
    if "element" in extension:
        properties["element"] = _field_from_frictionless_dict(
            extension["element"], path=f"{path}.x-mountainash.element",
        )
    if "dimensions" in extension:
        raw_dimensions = extension["dimensions"]
        properties["dimensions"] = (
            SchemaTypeStatus.UNKNOWN if raw_dimensions == {"kind": "unknown"} else tuple(raw_dimensions)
        )
    if "dtype" in extension:
        properties["dtype"] = _dtype_from_extension(path, extension["dtype"])
    try:
        return FieldSpec(**properties)
    except InvalidDtypeDeclaration as exc:
        raise InvalidDtypeDeclaration(path, exc.reason, exc.rejected_value) from exc
    except (TypeSpecError, ValueError, TypeError) as exc:
        raise InvalidDescriptorStructure(
            f"{path}: {exc}", descriptor_kind="schema", descriptor_path=path,
        ) from exc


def typespec_from_frictionless(data: Mapping[str, Any]) -> TypeSpec:
    """Create a TypeSpec from a resolved Frictionless Table Schema mapping.

    The v2 descriptor codec resolves JSON text and path references before
    calling this adapter. Direct callers must provide a schema mapping.

    Args:
        data: A resolved Frictionless Table Schema descriptor mapping.

    Returns:
        A TypeSpec populated from the descriptor.

    Notes:
        - Missing field types default to ``any``.
        - Omitted schema-level ``missingValues`` defaults to ``[""]``.
        - Unknown extension keys (other than ``x-mountainash``) are silently
          ignored.
    """
    if not isinstance(data, Mapping):
        raise TypeError("typespec_from_frictionless() requires a resolved schema mapping")

    descriptor = data
    _validate_declaration_descriptor(descriptor)
    # -- Spec-level fields --
    title: Optional[str] = descriptor.get("title")
    description: Optional[str] = descriptor.get("description")

    raw_primary_key = descriptor.get("primaryKey")
    primary_key = (
        None
        if raw_primary_key is None
        else _normalize_key_fields(raw_primary_key, "primary_key", allow_bare_string=True)
    )

    raw_unique_keys = descriptor.get("uniqueKeys")  # Gap 4
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
    schema_url: Optional[str] = descriptor.get("$schema")

    # Spec-level x-mountainash extensions. ``fields_match: "open"`` is the
    # mountainash-only extension form (see write path); ``contract`` (item 48)
    # is validated eagerly so a malformed descriptor fails fast on load.
    spec_ext: Dict[str, Any] = descriptor.get("x-mountainash", {}) or {}
    fields_match: str = _normalize_fields_match(descriptor, spec_ext)
    contract: Optional[Dict[str, str]] = spec_ext.get("contract") or None
    if contract is not None:
        validate_contract_dict(contract)
    # Foreign keys
    foreign_keys: Optional[List[ForeignKey]] = (
        list(parse_foreign_keys_at(descriptor, location=InvariantLocation("$")))
        if "foreignKeys" in descriptor
        else None
    )

    # -- Fields --
    fields = _fields_from_frictionless(descriptor.get("fields", []), "$.fields")

    return TypeSpec(
        fields=fields,
        title=title,
        description=description,
        primary_key=primary_key,
        foreign_keys=foreign_keys,
        missing_values=missing_values,
        fields_match=fields_match,
        unique_keys=unique_keys,
        schema_url=schema_url,
        contract=contract,
    )


def _migration_members(raw: Any, path: str) -> dict[str, dict]:
    if not isinstance(raw, list):
        raise InvalidDescriptorStructure(
            f"{path}: fields must be a list", descriptor_path=path, rejected_value=raw,
        )
    members = {}
    for index, child in enumerate(raw):
        location = f"{path}[{index}]"
        if not isinstance(child, Mapping) or not isinstance(child.get("name"), str):
            raise InvalidDescriptorStructure(
                f"{location}: named field required", descriptor_path=location, rejected_value=child,
            )
        name = child["name"]
        if name in members:
            raise InvalidDescriptorStructure(
                f"{location}.name: duplicate field name {name!r}", descriptor_path=f"{location}.name",
            )
        members[name] = _migrate_field_body(child, location)
    return members


def _migration_dtype(raw: Mapping[str, Any], path: str) -> Any:
    """Read only portable type intent; native overrides and metadata stay separate."""
    from .converters import resolve_field_canonical

    extension = raw.get("x-mountainash", {})
    if "dtype" in extension:
        return _dtype_from_extension(path, extension["dtype"])
    if "fields" in extension:
        return StructDtype(tuple(
            (child["name"], _migration_dtype(child, path) or SchemaTypeStatus.UNKNOWN)
            for child in extension["fields"]
        ))
    if "element" in extension:
        element = _migration_dtype(extension["element"], path) or SchemaTypeStatus.UNKNOWN
        dimensions = extension.get("dimensions")
        if dimensions is None:
            return ListDtype(element)
        return ArrayDtype(
            element, SchemaTypeStatus.UNKNOWN if dimensions == {"kind": "unknown"} else tuple(dimensions),
        )
    return resolve_field_canonical(FieldSpec(
        type=parse_universal(raw.get("type", "any")),
        format=raw.get("format", "default").removeprefix("fmt:"),
    ))


def _migrate_field_body(
    raw: Mapping[str, Any], path: str, *, parent_dtype: Any = None,
) -> dict[str, Any]:
    from mountainash.core.dtypes import resolve_dtype_parameters

    result = deepcopy(dict(raw))
    extension = result.get("x-mountainash", {})
    has_legacy = "object_fields" in extension or "item_object_fields" in extension
    members = None
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
    old_fields = extension.pop("object_fields", None)
    old_items = extension.pop("item_object_fields", None)
    if old_fields is not None:
        members = _migration_members(old_fields, f"{path}.x-mountainash.object_fields")
        evidence = StructDtype(tuple(
            (name, _migration_dtype(child, path) or SchemaTypeStatus.UNKNOWN)
            for name, child in members.items()
        ))
        if selected is None or selected is SchemaTypeStatus.UNKNOWN or selected is MountainashDtype.STRUCT:
            selected = evidence
        elif isinstance(selected, StructDtype):
            selected = resolve_dtype_parameters(selected, evidence)
    element_body = extension.get("element")
    if old_items is not None:
        item_members = _migration_members(old_items, f"{path}.x-mountainash.item_object_fields")
        element_body = {"type": "object", "x-mountainash": {"fields": list(item_members.values())}}
        evidence = ListDtype(_migration_dtype(element_body, path))
        if selected is None or selected is SchemaTypeStatus.UNKNOWN or selected is MountainashDtype.LIST:
            selected = evidence
        elif isinstance(selected, (ListDtype, ArrayDtype)):
            selected = resolve_dtype_parameters(selected, evidence)
    # Canonical type/order wins, while metadata and unrelated custom properties
    # remain on their original named declaration. Never roundtrip the whole body
    # through the typed codec: its supported-property inventory is intentionally narrower.
    lexical = raw.get("type") == "list" and isinstance(selected, ListDtype)
    portable = _field_to_frictionless_dict(
        FieldSpec(dtype=selected, type=UniversalType.LIST if lexical else UniversalType.ANY),
        path=path,
    )
    for key in ("type", "format"):
        if key in portable:
            result[key] = portable[key]
    for key in ("dtype", "fields", "element", "dimensions"):
        extension.pop(key, None)
    canonical = portable.get("x-mountainash", {})
    extension.update(canonical)
    if isinstance(selected, StructDtype) and selected.fields is not SchemaTypeStatus.UNKNOWN:
        candidates = members or {}
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
    """Return an owned descriptor with retired nested declarations explicitly migrated.

    Native string overrides remain authoritative. Portable parent shape/order and
    known child types win; compatible child declarations supply missing parameters.
    No files, references, packages or backend execution are involved.
    """
    if not isinstance(schema_descriptor, Mapping):
        raise TypeError("migrate_nested_field_declarations() requires a schema mapping")
    migrated = deepcopy(dict(schema_descriptor))
    if "fields" in migrated:
        migrated["fields"] = list(_migration_members(migrated["fields"], "$.fields").values())
    return migrated


__all__ = [
    "typespec_to_frictionless",
    "typespec_from_frictionless",
    "migrate_nested_field_declarations",
    "foreign_key_from_dict",
    "foreign_key_to_dict",
    "_constraints_to_dict",
    "_parse_constraints",
]
