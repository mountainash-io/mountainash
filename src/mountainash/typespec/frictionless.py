"""
Frictionless Table Schema import/export for TypeSpec.

Provides two public functions:
- typespec_to_frictionless(spec) → dict
- typespec_from_frictionless(data) → TypeSpec

Mountainash-specific extensions (rename_from, null_fill, keep_only_mapped)
are stored under the ``x-mountainash`` namespace key, following the
Frictionless custom extension convention.

Reference: https://specs.frictionlessdata.io/table-schema/
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .spec import FieldConstraints, FieldSpec, ForeignKey, ForeignKeyReference, TypeSpec
from .universal_types import UniversalType, normalize_type


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
    if constraints.min_length is not None:
        result["minLength"] = constraints.min_length
    if constraints.max_length is not None:
        result["maxLength"] = constraints.max_length
    if constraints.pattern is not None:
        result["pattern"] = constraints.pattern
    if constraints.enum is not None:
        result["enum"] = constraints.enum
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
        min_length=data.get("minLength"),
        max_length=data.get("maxLength"),
        pattern=data.get("pattern"),
        enum=data.get("enum"),
        enum_weights=enum_weights,
    )


# ---------------------------------------------------------------------------
# Export: TypeSpec → Frictionless dict
# ---------------------------------------------------------------------------

def typespec_to_frictionless(spec: TypeSpec) -> Dict[str, Any]:
    """Convert a TypeSpec to a Frictionless Table Schema descriptor dict.

    Standard Frictionless fields are placed at their canonical locations.
    Mountainash extensions (rename_from, null_fill per-field; keep_only_mapped
    at spec level) are stored under ``x-mountainash`` keys — added only when
    there are actual extensions to store.

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
        descriptor["primaryKey"] = spec.primary_key
    if spec.fields_match is not None:  # Gap 3
        descriptor["fieldsMatch"] = spec.fields_match
    if spec.unique_keys is not None:  # Gap 4
        descriptor["uniqueKeys"] = spec.unique_keys

    # Foreign keys (standard Frictionless field)
    if spec.foreign_keys:
        fk_list = []
        for fk in spec.foreign_keys:
            fk_list.append({
                "fields": fk.fields,
                "reference": {
                    "resource": fk.reference.resource,
                    "fields": fk.reference.fields,
                },
            })
        descriptor["foreignKeys"] = fk_list

    # Gap 1: missingValues (schema-level) — emit if non-default (non-empty list)
    if spec.missing_values is not None and spec.missing_values != [""]:
        descriptor["missingValues"] = spec.missing_values

    # Spec-level x-mountainash
    spec_extensions: Dict[str, Any] = {}
    if spec.keep_only_mapped:
        spec_extensions["keep_only_mapped"] = spec.keep_only_mapped
    if spec_extensions:
        descriptor["x-mountainash"] = spec_extensions

    # Fields
    fields_list: List[Dict[str, Any]] = []
    for fspec in spec.fields:
        field_dict: Dict[str, Any] = {
            "name": fspec.name,
            "type": fspec.type.value if isinstance(fspec.type, UniversalType) else str(fspec.type),
        }

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
            field_dict["missingValues"] = fspec.missing_values
        if fspec.categories is not None:  # Gap 7
            field_dict["categories"] = fspec.categories
        if fspec.true_values is not None:  # Gap 9
            field_dict["trueValues"] = fspec.true_values
        if fspec.false_values is not None:  # Gap 9
            field_dict["falseValues"] = fspec.false_values

        # Field-level x-mountainash extensions
        field_extensions: Dict[str, Any] = {}
        if fspec.rename_from is not None:
            field_extensions["rename_from"] = fspec.rename_from
        if fspec.null_fill is not None:
            field_extensions["null_fill"] = fspec.null_fill
        if fspec.custom_cast is not None:
            field_extensions["custom_cast"] = fspec.custom_cast
        if fspec.constraints and fspec.constraints.enum_weights is not None:
            field_extensions["enum_weights"] = fspec.constraints.enum_weights
        if fspec.backend_type is not None:  # Gap 10: move under x-mountainash
            field_extensions["backend_type"] = fspec.backend_type
        if field_extensions:
            field_dict["x-mountainash"] = field_extensions

        fields_list.append(field_dict)

    descriptor["fields"] = fields_list
    return descriptor


# ---------------------------------------------------------------------------
# Import: Frictionless dict / JSON string / Path → TypeSpec
# ---------------------------------------------------------------------------

def typespec_from_frictionless(data: Union[Dict[str, Any], str, Path]) -> TypeSpec:
    """Create a TypeSpec from a Frictionless Table Schema descriptor.

    Args:
        data: One of:
            - A dict (Frictionless descriptor)
            - A JSON string
            - A pathlib.Path or path string pointing to a JSON file

    Returns:
        A TypeSpec populated from the descriptor.

    Notes:
        - Missing field types default to ``string``.
        - Unknown extension keys (other than ``x-mountainash``) are silently
          ignored.
    """
    descriptor: Dict[str, Any]

    if isinstance(data, Path):
        descriptor = json.loads(data.read_text(encoding="utf-8"))
    elif isinstance(data, str):
        # Determine whether it's a file path or a raw JSON string
        p = Path(data)
        if p.exists():
            descriptor = json.loads(p.read_text(encoding="utf-8"))
        else:
            descriptor = json.loads(data)
    else:
        descriptor = data

    # -- Spec-level fields --
    title: Optional[str] = descriptor.get("title")
    description: Optional[str] = descriptor.get("description")
    primary_key = descriptor.get("primaryKey")
    missing_values: Optional[List[str]] = descriptor.get("missingValues")
    fields_match: Optional[str] = descriptor.get("fieldsMatch")  # Gap 3
    unique_keys: Optional[List[List[str]]] = descriptor.get("uniqueKeys")  # Gap 4

    # Spec-level x-mountainash extensions
    spec_ext: Dict[str, Any] = descriptor.get("x-mountainash", {}) or {}
    keep_only_mapped: bool = bool(spec_ext.get("keep_only_mapped", False))

    # Foreign keys
    raw_fks = descriptor.get("foreignKeys")
    foreign_keys: Optional[List[ForeignKey]] = None
    if raw_fks:
        foreign_keys = []
        for raw_fk in raw_fks:
            ref = raw_fk["reference"]
            foreign_keys.append(
                ForeignKey(
                    fields=raw_fk["fields"],
                    reference=ForeignKeyReference(
                        resource=ref["resource"],
                        fields=ref["fields"],
                    ),
                )
            )

    # -- Fields --
    fields: List[FieldSpec] = []
    for raw_field in descriptor.get("fields", []):
        name: str = raw_field["name"]
        type_str: str = raw_field.get("type", "string")
        universal_type = normalize_type(type_str)

        format_: str = raw_field.get("format", "default")
        field_title: Optional[str] = raw_field.get("title")
        field_description: Optional[str] = raw_field.get("description")
        field_missing_values: Optional[List[str]] = raw_field.get("missingValues")
        categories: Optional[List[Any]] = raw_field.get("categories")  # Gap 7
        true_values: Optional[List[str]] = raw_field.get("trueValues")  # Gap 9
        false_values: Optional[List[str]] = raw_field.get("falseValues")  # Gap 9

        # Field-level x-mountainash extensions
        field_ext: Dict[str, Any] = raw_field.get("x-mountainash", {}) or {}
        rename_from: Optional[str] = field_ext.get("rename_from")
        null_fill: Any = field_ext.get("null_fill")
        custom_cast: Optional[str] = field_ext.get("custom_cast")
        enum_weights: Optional[Dict[str, float]] = field_ext.get("enum_weights")
        backend_type: Optional[str] = field_ext.get("backend_type")  # Gap 10

        constraints = _parse_constraints(raw_field.get("constraints"), enum_weights=enum_weights)

        fields.append(
            FieldSpec(
                name=name,
                type=universal_type,
                format=format_,
                title=field_title,
                description=field_description,
                constraints=constraints,
                missing_values=field_missing_values,
                categories=categories,
                true_values=true_values,
                false_values=false_values,
                backend_type=backend_type,
                rename_from=rename_from,
                null_fill=null_fill,
                custom_cast=custom_cast,
            )
        )

    return TypeSpec(
        fields=fields,
        title=title,
        description=description,
        primary_key=primary_key,
        foreign_keys=foreign_keys,
        missing_values=missing_values,
        keep_only_mapped=keep_only_mapped,
        fields_match=fields_match,
        unique_keys=unique_keys,
    )


# Aliases used by TypeSpec stubs in spec.py
to_frictionless = typespec_to_frictionless
from_frictionless = typespec_from_frictionless


__all__ = [
    "typespec_to_frictionless",
    "typespec_from_frictionless",
    "to_frictionless",
    "from_frictionless",
    "_constraints_to_dict",
    "_parse_constraints",
]
