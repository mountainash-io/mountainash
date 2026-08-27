"""Pure, deterministic semantic validation for operational TypeSpecs."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field as dataclass_field
import math
import re
from typing import Any

from mountainash.typespec.errors import (
    AmbiguousFieldName,
    InvalidConstraintDeclaration,
    InvalidFieldIdentifier,
    InvalidJSONSchemaConstraint,
    InvalidTypeSpecSemantics,
    TypeSpecError,
)
from mountainash.typespec.spec import (
    FieldConstraints,
    LabeledValue,
    FieldSpec,
    ForeignKey,
    TypeSpec,
)
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.jsonschema import compile_json_schema


@dataclass(frozen=True)
class TypeSpecIssue:
    """One declaration error with a stable pointer and machine-readable code."""
    path: str
    code: str
    message: str
    cause: TypeSpecError = dataclass_field(compare=False)


def _issue(
    issues: list[TypeSpecIssue],
    *,
    path: str,
    code: str,
    cause: TypeSpecError,
) -> None:
    issues.append(TypeSpecIssue(path=path, code=code, message=str(cause), cause=cause))


def _constraint_issue(
    issues: list[TypeSpecIssue], path: str, message: str
) -> None:
    _issue(
        issues,
        path=path,
        code="typespec.invalid_constraint_declaration",
        cause=InvalidConstraintDeclaration(message),
    )


def _validate_constraints(
    field: FieldSpec, path: str, issues: list[TypeSpecIssue]
) -> None:
    constraints = field.constraints
    if constraints is None:
        return
    if not isinstance(constraints, FieldConstraints):
        _constraint_issue(issues, f"{path}/constraints", "constraints must be FieldConstraints")
        return

    for name in ("required", "unique"):
        value = getattr(constraints, name)
        if type(value) is not bool:  # noqa: E721 — strict declaration shape
            _constraint_issue(issues, f"{path}/constraints/{name}", f"{name} must be bool")

    for name in ("min_length", "max_length"):
        value = getattr(constraints, name)
        if value is not None and (type(value) is not int or value < 0):  # noqa: E721 — bool is not an integer
            _constraint_issue(
                issues,
                f"{path}/constraints/{name}",
                f"{name} must be a non-negative integer",
            )
    if (
        type(constraints.min_length) is int  # noqa: E721 — strict declaration shape
        and type(constraints.max_length) is int  # noqa: E721 — strict declaration shape
        and constraints.min_length > constraints.max_length
    ):
        _constraint_issue(
            issues,
            f"{path}/constraints",
            "min_length must not exceed max_length",
        )

    allowed: dict[str, frozenset[UniversalType]] = {
        "min_length": frozenset(
            {UniversalType.STRING, UniversalType.ARRAY, UniversalType.OBJECT, UniversalType.GEOJSON}
        ),
        "max_length": frozenset(
            {UniversalType.STRING, UniversalType.ARRAY, UniversalType.OBJECT, UniversalType.GEOJSON}
        ),
        "minimum": frozenset(
            {
                UniversalType.INTEGER,
                UniversalType.NUMBER,
                UniversalType.DATE,
                UniversalType.TIME,
                UniversalType.DATETIME,
                UniversalType.DURATION,
                UniversalType.YEAR,
                UniversalType.YEARMONTH,
            }
        ),
        "maximum": frozenset(
            {
                UniversalType.INTEGER,
                UniversalType.NUMBER,
                UniversalType.DATE,
                UniversalType.TIME,
                UniversalType.DATETIME,
                UniversalType.DURATION,
                UniversalType.YEAR,
                UniversalType.YEARMONTH,
            }
        ),
        "exclusive_minimum": frozenset(
            {
                UniversalType.INTEGER,
                UniversalType.NUMBER,
                UniversalType.DATE,
                UniversalType.TIME,
                UniversalType.DATETIME,
                UniversalType.DURATION,
                UniversalType.YEAR,
                UniversalType.YEARMONTH,
            }
        ),
        "exclusive_maximum": frozenset(
            {
                UniversalType.INTEGER,
                UniversalType.NUMBER,
                UniversalType.DATE,
                UniversalType.TIME,
                UniversalType.DATETIME,
                UniversalType.DURATION,
                UniversalType.YEAR,
                UniversalType.YEARMONTH,
            }
        ),
        "pattern": frozenset({UniversalType.STRING}),
        "json_schema": frozenset({UniversalType.ARRAY, UniversalType.OBJECT}),
    }
    for name, types in allowed.items():
        value = getattr(constraints, name)
        if value is not None and field.type not in types:
            _constraint_issue(
                issues,
                f"{path}/constraints/{name}",
                f"{name} is not valid for {field.type.value!r}",
            )

    if constraints.pattern is not None:
        if not isinstance(constraints.pattern, str):
            _constraint_issue(issues, f"{path}/constraints/pattern", "pattern must be text")
        else:
            try:
                re.compile(constraints.pattern)
            except re.error as error:
                _constraint_issue(issues, f"{path}/constraints/pattern", str(error))

    if constraints.enum is not None:
        if not isinstance(constraints.enum, list) or not constraints.enum:
            _constraint_issue(issues, f"{path}/constraints/enum", "enum must be a non-empty list")

    if constraints.json_schema is not None:
        try:
            compile_json_schema(constraints.json_schema)
        except InvalidJSONSchemaConstraint as error:
            _issue(
                issues,
                path=f"{path}/constraints/json_schema",
                code="typespec.invalid_json_schema_constraint",
                cause=error,
            )
        except TypeSpecError as error:
            _issue(
                issues,
                path=f"{path}/constraints/json_schema",
                code="typespec.invalid_json_schema_constraint",
                cause=error,
            )

    if constraints.enum_weights is not None:
        weights = constraints.enum_weights
        if not isinstance(weights, Mapping):
            _constraint_issue(issues, f"{path}/constraints/enum_weights", "enum_weights must be a mapping")
        else:
            for key, weight in weights.items():
                if not isinstance(key, str) or type(weight) not in {int, float} or not math.isfinite(weight) or weight < 0:
                    _constraint_issue(issues, f"{path}/constraints/enum_weights", "enum weights must be finite non-negative numbers")
                    break


def _validate_missing_values(values: Any, path: str, issues: list[TypeSpecIssue]) -> None:
    if values is None:
        return
    if not isinstance(values, list):
        _constraint_issue(issues, path, "missing_values must be a list")
        return
    seen_values: set[str] = set()
    seen_labels: set[str] = set()
    for index, item in enumerate(values):
        item_path = f"{path}/{index}"
        value = item.value if isinstance(item, LabeledValue) else item
        label = item.label if isinstance(item, LabeledValue) else None
        if not isinstance(value, str):
            _constraint_issue(issues, item_path, "missing value must be text")
            continue
        if value in seen_values:
            _constraint_issue(issues, item_path, "missing value is duplicated")
        seen_values.add(value)
        if label is not None:
            if not isinstance(label, str) or not label:
                _constraint_issue(issues, item_path, "missing-value label must be text")
            elif label in seen_labels:
                _constraint_issue(issues, item_path, "missing-value label is duplicated")
            seen_labels.add(label)


def _validate_field_properties(
    field: FieldSpec, path: str, issues: list[TypeSpecIssue]
) -> None:
    if not isinstance(field.format, str) or not field.format:
        _constraint_issue(issues, f"{path}/format", "format must be a non-empty string")
    elif field.format.startswith("fmt:"):
        _constraint_issue(
            issues,
            f"{path}/format",
            "format must not include the retired 'fmt:' prefix",
        )
    else:
        allowed_formats = {
            UniversalType.STRING: {"default", "email", "uri", "binary", "uuid"},
            UniversalType.DATE: {"default", "any"},
            UniversalType.TIME: {"default", "any"},
            UniversalType.DATETIME: {"default", "any"},
        }
        if field.type in allowed_formats:
            if field.format not in allowed_formats[field.type] and not (
                field.type in {UniversalType.DATE, UniversalType.TIME, UniversalType.DATETIME}
                and field.format
            ):
                _constraint_issue(
                    issues,
                    f"{path}/format",
                    f"format {field.format!r} is not valid for {field.type.value!r}",
                )
        elif field.format != "default":
            _constraint_issue(
                issues,
                f"{path}/format",
                f"{field.type.value!r} has no format variants",
            )

    if field.item_type is not None:
        allowed_item_types = {
            UniversalType.STRING.value,
            UniversalType.INTEGER.value,
            UniversalType.NUMBER.value,
            UniversalType.BOOLEAN.value,
            UniversalType.DATE.value,
            UniversalType.TIME.value,
            UniversalType.DATETIME.value,
        }
        if field.item_type not in allowed_item_types:
            _constraint_issue(
                issues,
                f"{path}/item_type",
                "item_type must be one of the supported primitive list item types",
            )
    if field.delimiter is not None and (
        not isinstance(field.delimiter, str) or not field.delimiter
    ):
        _constraint_issue(issues, f"{path}/delimiter", "delimiter must be a non-empty string")
    _validate_missing_values(field.missing_values, f"{path}/missing_values", issues)

    if field.decimal_char is not None and field.type is not UniversalType.NUMBER:
        _constraint_issue(
            issues,
            f"{path}/decimal_char",
            "decimal_char is valid only for number fields",
        )
    if field.group_char is not None and field.type not in {
        UniversalType.INTEGER,
        UniversalType.NUMBER,
    }:
        _constraint_issue(
            issues,
            f"{path}/group_char",
            "group_char is valid only for integer and number fields",
        )
    if field.bare_number is not None and field.type not in {
        UniversalType.INTEGER,
        UniversalType.NUMBER,
    }:
        _constraint_issue(
            issues,
            f"{path}/bare_number",
            "bare_number is valid only for integer and number fields",
        )

    if field.type is not UniversalType.BOOLEAN and (
        field.true_values is not None or field.false_values is not None
    ):
        _constraint_issue(
            issues,
            path,
            "true_values and false_values are valid only for boolean fields",
        )
    boolean_values: dict[str, set[str]] = {}
    for property_name in ("true_values", "false_values"):
        values = getattr(field, property_name)
        if values is None:
            continue
        property_path = f"{path}/{property_name}"
        if not isinstance(values, list) or not values or any(
            not isinstance(value, str) or not value for value in values
        ):
            _constraint_issue(
                issues,
                property_path,
                f"{property_name} must be a non-empty list of non-empty strings",
            )
            continue
        value_set = set(values)
        if len(value_set) != len(values):
            _constraint_issue(
                issues,
                property_path,
                f"{property_name} must not contain duplicates",
            )
        boolean_values[property_name] = value_set
    if boolean_values.get("true_values", set()) & boolean_values.get("false_values", set()):
        _constraint_issue(
            issues,
            f"{path}/false_values",
            "true_values and false_values must be disjoint",
        )

    if field.categories is not None:
        if field.type not in {UniversalType.STRING, UniversalType.INTEGER}:
            _constraint_issue(
                issues,
                f"{path}/categories",
                "categories are valid only for string and integer fields",
            )
        elif not isinstance(field.categories, list):
            _constraint_issue(issues, f"{path}/categories", "categories must be a list")
        else:
            seen_categories: set[tuple[type[Any], Any]] = set()
            labels: set[str] = set()
            for index, category in enumerate(field.categories):
                category_path = f"{path}/categories/{index}"
                value = category.value if isinstance(category, LabeledValue) else category
                label = category.label if isinstance(category, LabeledValue) else None
                if type(value) is not (
                    str if field.type is UniversalType.STRING else int
                ):
                    _constraint_issue(
                        issues,
                        category_path,
                        "category does not match the declared field type",
                    )
                    continue
                key = (type(value), value)
                if key in seen_categories:
                    _constraint_issue(issues, category_path, "category value is duplicated")
                seen_categories.add(key)
                if label is not None:
                    if not isinstance(label, str) or not label:
                        _constraint_issue(issues, category_path, "category label must be text")
                    elif label in labels:
                        _constraint_issue(issues, category_path, "category label is duplicated")
                    labels.add(label)
    if field.categories_ordered is not None:
        if field.categories is None:
            _constraint_issue(
                issues,
                f"{path}/categories_ordered",
                "categories_ordered requires categories",
            )
        elif type(field.categories_ordered) is not bool:  # noqa: E721 — strict declaration shape
            _constraint_issue(
                issues,
                f"{path}/categories_ordered",
                "categories_ordered must be bool",
            )


def _validate_field_list(
    fields: Any,
    *,
    path: str,
    issues: list[TypeSpecIssue],
) -> set[str]:
    if not isinstance(fields, list) or not fields:
        _constraint_issue(issues, path, "fields must be a non-empty list of FieldSpec")
        return set()

    names: set[str] = set()
    for index, field in enumerate(fields):
        field_path = f"{path}/{index}"
        if not isinstance(field, FieldSpec):
            _constraint_issue(issues, field_path, "field must be FieldSpec")
            continue
        if not isinstance(field.name, str) or not field.name:
            _issue(
                issues,
                path=f"{field_path}/name",
                code="typespec.invalid_field_identifier",
                cause=InvalidFieldIdentifier(field_path, "name", field.name),
            )
        elif field.name in names:
            _issue(
                issues,
                path=f"{field_path}/name",
                code="typespec.ambiguous_field_name",
                cause=AmbiguousFieldName(f"duplicate field name {field.name!r}"),
            )
        else:
            names.add(field.name)

        if field.rename_from is not None and (
            not isinstance(field.rename_from, str) or not field.rename_from
        ):
            _issue(
                issues,
                path=f"{field_path}/rename_from",
                code="typespec.invalid_field_identifier",
                cause=InvalidFieldIdentifier(field_path, "rename_from", field.rename_from),
            )

        _validate_constraints(field, field_path, issues)
        _validate_field_properties(field, field_path, issues)
        if field.object_fields is not None:
            _validate_field_list(
                field.object_fields,
                path=f"{field_path}/object_fields",
                issues=issues,
            )
        if field.item_object_fields is not None:
            _validate_field_list(
                field.item_object_fields,
                path=f"{field_path}/item_object_fields",
                issues=issues,
            )
    return names


def _validate_key(
    key: Any, *, path: str, known_names: set[str], issues: list[TypeSpecIssue]
) -> None:
    if not isinstance(key, list) or not key:
        _constraint_issue(issues, path, "key must be a non-empty list of field names")
        return
    seen: set[str] = set()
    for index, name in enumerate(key):
        entry_path = f"{path}/{index}"
        if not isinstance(name, str) or not name or name not in known_names:
            _constraint_issue(issues, entry_path, f"key field {name!r} is not declared")
        elif name in seen:
            _constraint_issue(issues, entry_path, f"key field {name!r} is duplicated")
        seen.add(name)


def _validate_relationships(
    spec: TypeSpec,
    *,
    resource_name: str | None,
    package_resource_names: frozenset[str] | None,
    package_specs: Mapping[str, TypeSpec] | None,
    known_names: set[str],
    issues: list[TypeSpecIssue],
) -> None:
    foreign_keys = spec.foreign_keys
    if foreign_keys is None:
        return
    if not isinstance(foreign_keys, list) or not foreign_keys:
        _constraint_issue(issues, "/foreign_keys", "foreign_keys must be a non-empty list")
        return
    for index, foreign_key in enumerate(foreign_keys):
        path = f"/foreign_keys/{index}"
        if not isinstance(foreign_key, ForeignKey):
            _constraint_issue(issues, path, "foreign key must be ForeignKey")
            continue
        _validate_key(foreign_key.fields, path=f"{path}/fields", known_names=known_names, issues=issues)
        reference = foreign_key.reference
        target = resource_name if reference.resource is None else reference.resource
        if package_resource_names is not None and target is not None and target not in package_resource_names:
            _constraint_issue(issues, f"{path}/reference/resource", f"resource {target!r} is not in the package")
        if len(foreign_key.fields) != len(reference.fields):
            _constraint_issue(issues, path, "foreign key child and parent arity differ")
        target_spec = (
            package_specs.get(target)
            if package_specs is not None and target is not None
            else spec
            if target == resource_name
            else None
        )
        if target_spec is not None:
            target_names = {field.name for field in target_spec.fields if isinstance(field.name, str)}
            _validate_key(reference.fields, path=f"{path}/reference/fields", known_names=target_names, issues=issues)


def validate_typespec_semantics(
    spec: TypeSpec,
    *,
    resource_name: str | None = None,
    package_resource_names: frozenset[str] | None = None,
    package_specs: Mapping[str, TypeSpec] | None = None,
) -> tuple[TypeSpecIssue, ...]:
    """Return all semantic declaration issues in deterministic pointer order."""
    issues: list[TypeSpecIssue] = []
    known_names = _validate_field_list(spec.fields, path="/fields", issues=issues)
    _validate_missing_values(spec.missing_values, "/missing_values", issues)

    if spec.fields_match not in {"exact", "equal", "subset", "superset", "partial", "open"}:
        _constraint_issue(issues, "/fields_match", "fields_match is not a supported mode")
    if spec.primary_key is not None:
        _validate_key(spec.primary_key, path="/primary_key", known_names=known_names, issues=issues)
    if spec.unique_keys is not None:
        if not isinstance(spec.unique_keys, list) or not spec.unique_keys:
            _constraint_issue(issues, "/unique_keys", "unique_keys must be a non-empty list")
        else:
            for index, key in enumerate(spec.unique_keys):
                _validate_key(key, path=f"/unique_keys/{index}", known_names=known_names, issues=issues)
    if package_resource_names is not None and package_specs is not None:
        _validate_relationships(
            spec,
            resource_name=resource_name,
            package_resource_names=package_resource_names,
            package_specs=package_specs,
            known_names=known_names,
            issues=issues,
        )
    elif spec.foreign_keys is not None:
        _validate_relationships(
            spec,
            resource_name=resource_name,
            package_resource_names=None,
            package_specs=None,
            known_names=known_names,
            issues=issues,
        )
    return tuple(sorted(issues, key=lambda issue: (issue.path, issue.code)))


def require_valid_typespec(
    spec: TypeSpec,
    *,
    resource_name: str | None = None,
    package_resource_names: frozenset[str] | None = None,
    package_specs: Mapping[str, TypeSpec] | None = None,
) -> None:
    """Raise one aggregate error before a declared schema can execute."""
    issues = validate_typespec_semantics(
        spec,
        resource_name=resource_name,
        package_resource_names=package_resource_names,
        package_specs=package_specs,
    )
    if issues:
        raise InvalidTypeSpecSemantics(issues, resource_name)


__all__ = ["TypeSpecIssue", "require_valid_typespec", "validate_typespec_semantics"]
