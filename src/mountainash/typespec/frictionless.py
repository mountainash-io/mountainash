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
from typing import Any, Dict, List, Optional

from mountainash.conform.contract import validate_contract_dict

from .errors import InvalidFieldMatchDeclaration, InvalidKeyShapeError
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
        if extension != "open":
            raise InvalidFieldMatchDeclaration(
                None, extension, "x-mountainash.fields_match must be 'open'"
            )
        return "open"
    if has_standard:
        if standard not in _STANDARD_FIELDS_MATCH:
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

def _constraints_to_dict(constraints: FieldConstraints) -> dict:
    """Serialize FieldConstraints → Frictionless-compatible dict (camelCase keys)."""
    result: Dict[str, Any] = {}
    if constraints.required:
        result["required"] = constraints.required
    if constraints.unique:
        result["unique"] = constraints.unique
    if constraints.minimum is not None:
        result["minimum"] = constraints.minimum
    if constraints.maximum is not None:
        result["maximum"] = constraints.maximum
    if constraints.exclusive_minimum is not None:
        result["exclusiveMinimum"] = constraints.exclusive_minimum
    if constraints.exclusive_maximum is not None:
        result["exclusiveMaximum"] = constraints.exclusive_maximum
    if constraints.min_length is not None:
        result["minLength"] = constraints.min_length
    if constraints.max_length is not None:
        result["maxLength"] = constraints.max_length
    if constraints.pattern is not None:
        result["pattern"] = constraints.pattern
    if constraints.enum is not None:
        result["enum"] = constraints.enum
    if constraints.json_schema is not None:
        result["jsonSchema"] = constraints.json_schema
    return result


def _parse_constraints(
    data: Optional[Dict[str, Any]],
    enum_weights: Optional[Dict[str, float]] = None,
) -> Optional[FieldConstraints]:
    """Deserialize a Frictionless constraints dict → FieldConstraints (or None)."""
    if not data and not enum_weights:
        return None
    if not data:
        data = {}
    return FieldConstraints(
        required=data.get("required", False),
        unique=data.get("unique", False),
        minimum=data.get("minimum"),
        maximum=data.get("maximum"),
        exclusive_minimum=data.get("exclusiveMinimum"),
        exclusive_maximum=data.get("exclusiveMaximum"),
        min_length=data.get("minLength"),
        max_length=data.get("maxLength"),
        pattern=data.get("pattern"),
        enum=data.get("enum"),
        enum_weights=enum_weights,
        json_schema=data.get("jsonSchema"),
    )


# ---------------------------------------------------------------------------
# Export: TypeSpec → Frictionless dict
# ---------------------------------------------------------------------------

def _field_to_frictionless_dict(fspec: "FieldSpec") -> Dict[str, Any]:
    """Export one FieldSpec to a Frictionless field descriptor dict.

    Recurses into ``object_fields`` and ``item_object_fields`` (item 102) so
    nested fields retain the complete field descriptor shape of top-level
    fields. The ``type`` key is omitted exactly when the type is ``ANY``
    (spec-faithful — the absence of a ``type`` property means type "any").
    """
    field_dict: Dict[str, Any] = {"name": fspec.name}
    if fspec.type is not UniversalType.ANY:
        field_dict["type"] = (
            fspec.type.value if isinstance(fspec.type, UniversalType) else str(fspec.type)
        )

    if fspec.format != "default":
        field_dict["format"] = fspec.format
    if fspec.title:
        field_dict["title"] = fspec.title
    if fspec.description:
        field_dict["description"] = fspec.description
    if fspec.constraints is not None:
        constraints_dict = _constraints_to_dict(fspec.constraints)
        if constraints_dict:
            field_dict["constraints"] = constraints_dict
    if fspec.missing_values is not None:
        field_dict["missingValues"] = [
            _missing_value_to_json(mv) for mv in fspec.missing_values
        ]
    if fspec.categories is not None:
        field_dict["categories"] = [_category_to_json(c) for c in fspec.categories]
    if fspec.true_values is not None:
        field_dict["trueValues"] = fspec.true_values
    if fspec.false_values is not None:
        field_dict["falseValues"] = fspec.false_values
    if fspec.categories_ordered is not None:
        field_dict["categoriesOrdered"] = fspec.categories_ordered
    if fspec.example is not None:
        field_dict["example"] = fspec.example
    if fspec.rdf_type is not None:
        field_dict["rdfType"] = fspec.rdf_type
    if fspec.decimal_char is not None:
        field_dict["decimalChar"] = fspec.decimal_char
    if fspec.group_char is not None:
        field_dict["groupChar"] = fspec.group_char
    if fspec.bare_number is not None:
        field_dict["bareNumber"] = fspec.bare_number
    if fspec.item_type is not None:
        field_dict["itemType"] = fspec.item_type
    if fspec.delimiter is not None:
        field_dict["delimiter"] = fspec.delimiter

    field_extensions: Dict[str, Any] = {}
    if fspec.rename_from is not None:
        field_extensions["rename_from"] = fspec.rename_from
    if fspec.null_fill is not None:
        field_extensions["null_fill"] = fspec.null_fill
    if fspec.custom_cast is not None:
        field_extensions["custom_cast"] = fspec.custom_cast
    if fspec.constraints and fspec.constraints.enum_weights is not None:
        field_extensions["enum_weights"] = fspec.constraints.enum_weights
    if fspec.backend_type is not None:
        field_extensions["backend_type"] = fspec.backend_type
    if fspec.object_fields is not None:
        field_extensions["object_fields"] = [
            _field_to_frictionless_dict(inner) for inner in fspec.object_fields
        ]
    if fspec.item_object_fields is not None:
        field_extensions["item_object_fields"] = [
            _field_to_frictionless_dict(inner) for inner in fspec.item_object_fields
        ]
    if field_extensions:
        field_dict["x-mountainash"] = field_extensions

    return field_dict


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
    fields_list: List[Dict[str, Any]] = [
        _field_to_frictionless_dict(fspec) for fspec in spec.fields
    ]

    descriptor["fields"] = fields_list
    return descriptor


# Import: resolved Frictionless schema mapping → TypeSpec
# ---------------------------------------------------------------------------

def _field_from_frictionless_dict(raw_field: Mapping[str, Any]) -> "FieldSpec":
    """Import one Frictionless field descriptor into a FieldSpec.

    Recurses into ``x-mountainash.object_fields`` / ``item_object_fields``
    (item 102) so nested descriptors mirror the export helper exactly. An
    absent ``type`` defaults to ``any``; a leading ``fmt:`` prefix on the
    temporal format is normalized off at this boundary.
    """
    name: str = raw_field["name"]
    type_str: str = raw_field.get("type", "any")
    universal_type = parse_universal(type_str)

    raw_format: str = raw_field.get("format", "default")
    format_: str = raw_format.removeprefix("fmt:")
    field_title: Optional[str] = raw_field.get("title")
    field_description: Optional[str] = raw_field.get("description")
    field_missing_values: Optional[List[MissingValue]] = (
        [_missing_value_from_json(mv) for mv in raw_field["missingValues"]]
        if "missingValues" in raw_field else None
    )
    categories: Optional[List[Any]] = (
        [_category_from_json(c) for c in raw_field["categories"]]
        if "categories" in raw_field else None
    )
    true_values: Optional[List[str]] = raw_field.get("trueValues")
    false_values: Optional[List[str]] = raw_field.get("falseValues")
    categories_ordered: Optional[bool] = raw_field.get("categoriesOrdered")
    example: Optional[Any] = raw_field.get("example")
    rdf_type: Optional[str] = raw_field.get("rdfType")
    decimal_char: Optional[str] = raw_field.get("decimalChar")
    group_char: Optional[str] = raw_field.get("groupChar")
    bare_number: Optional[bool] = raw_field.get("bareNumber")
    item_type: Optional[str] = raw_field.get("itemType")
    delimiter: Optional[str] = raw_field.get("delimiter")

    field_ext: Dict[str, Any] = raw_field.get("x-mountainash", {}) or {}
    rename_from: Optional[str] = field_ext.get("rename_from")
    null_fill: Any = field_ext.get("null_fill")
    custom_cast: Optional[str] = field_ext.get("custom_cast")
    enum_weights: Optional[Dict[str, float]] = field_ext.get("enum_weights")
    backend_type: Optional[str] = field_ext.get("backend_type")
    raw_object_fields: Optional[List[Dict[str, Any]]] = field_ext.get("object_fields")
    object_fields: Optional[List[FieldSpec]] = (
        [_field_from_frictionless_dict(rf) for rf in raw_object_fields]
        if raw_object_fields is not None else None
    )
    raw_item_object_fields: Optional[List[Dict[str, Any]]] = field_ext.get("item_object_fields")
    item_object_fields: Optional[List[FieldSpec]] = (
        [_field_from_frictionless_dict(rf) for rf in raw_item_object_fields]
        if raw_item_object_fields is not None else None
    )

    constraints = _parse_constraints(raw_field.get("constraints"), enum_weights=enum_weights)

    return FieldSpec(
        name=name,
        type=universal_type,
        format=format_,
        title=field_title,
        description=field_description,
        constraints=constraints,
        missing_values=field_missing_values,
        categories=categories,
        categories_ordered=categories_ordered,
        example=example,
        rdf_type=rdf_type,
        decimal_char=decimal_char,
        group_char=group_char,
        bare_number=bare_number,
        item_type=item_type,
        delimiter=delimiter,
        true_values=true_values,
        false_values=false_values,
        backend_type=backend_type,
        rename_from=rename_from,
        null_fill=null_fill,
        custom_cast=custom_cast,
        object_fields=object_fields,
        item_object_fields=item_object_fields,
    )


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
    raw_fks = descriptor.get("foreignKeys")
    foreign_keys: Optional[List[ForeignKey]] = None
    if raw_fks:
        foreign_keys = [foreign_key_from_dict(raw_fk) for raw_fk in raw_fks]

    # -- Fields --
    fields: List[FieldSpec] = [
        _field_from_frictionless_dict(raw_field)
        for raw_field in descriptor.get("fields", [])
    ]

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


__all__ = [
    "typespec_to_frictionless",
    "typespec_from_frictionless",
    "foreign_key_from_dict",
    "foreign_key_to_dict",
    "_constraints_to_dict",
    "_parse_constraints",
]
