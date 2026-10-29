"""Pure, deterministic semantic validation for operational TableSchemas."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field as dataclass_field, fields as dataclass_fields
from enum import Enum, auto
import math
import re
from types import MappingProxyType
from typing import Any

from mountainash.core.dtypes import SchemaTypeStatus
from mountainash.typespec.errors import (
    InvalidConstraintDeclaration,
    InvalidFieldIdentifier,
    InvalidJSONSchemaConstraint,
    InvalidTypeSpecSemantics,
    TypeSpecError,
)
from mountainash.typespec.spec import (
    FieldConstraints,
    FieldDefinition,
    ForeignKey,
    LabeledValue,
    TableSchema,
)
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.jsonschema import compile_json_schema



class ValidationImplementationKind(Enum):
    """Execution disposition for one field-type and constraint pair."""

    EXPRESSION_CHECK = auto()
    VALUE_CHECK = auto()
    DECLARATION_ONLY = auto()
    METADATA_ONLY = auto()
    UNSUPPORTED = auto()


# An unspecified type (ANY) is a legitimate partial declaration: a constraint
# neither invents a physical type nor is refused for the lack of one. Its checks
# run against whatever logical value is present (a value of an unsuitable kind
# fails the check rather than being silently accepted).
_RANGE_TYPES = frozenset(
    {
        UniversalType.ANY,
        UniversalType.INTEGER,
        UniversalType.NUMBER,
        UniversalType.DATE,
        UniversalType.TIME,
        UniversalType.DATETIME,
        UniversalType.DURATION,
        UniversalType.YEAR,
        UniversalType.YEARMONTH,
    }
)
_LENGTH_TYPES = frozenset(
    {
        UniversalType.ANY,
        UniversalType.STRING,
        UniversalType.ARRAY,
        UniversalType.OBJECT,
        UniversalType.GEOJSON,
    }
)
_STRING_TYPES = frozenset({UniversalType.ANY, UniversalType.STRING})
_JSON_SCHEMA_TYPES = frozenset({UniversalType.ANY, UniversalType.ARRAY, UniversalType.OBJECT})


def _implementation_kind(
    field_type: UniversalType, constraint: str
) -> ValidationImplementationKind:
    if constraint == "required":
        return ValidationImplementationKind.EXPRESSION_CHECK
    if constraint in {"unique", "enum"}:
        return ValidationImplementationKind.VALUE_CHECK
    if constraint in {"minimum", "maximum", "exclusive_minimum", "exclusive_maximum"}:
        return (
            ValidationImplementationKind.VALUE_CHECK
            if field_type in _RANGE_TYPES
            else ValidationImplementationKind.UNSUPPORTED
        )
    if constraint in {"min_length", "max_length"}:
        return (
            ValidationImplementationKind.VALUE_CHECK
            if field_type in _LENGTH_TYPES
            else ValidationImplementationKind.UNSUPPORTED
        )
    if constraint == "pattern":
        return (
            ValidationImplementationKind.VALUE_CHECK
            if field_type in _STRING_TYPES
            else ValidationImplementationKind.UNSUPPORTED
        )
    if constraint == "json_schema":
        return (
            ValidationImplementationKind.VALUE_CHECK
            if field_type in _JSON_SCHEMA_TYPES
            else ValidationImplementationKind.UNSUPPORTED
        )
    if constraint in {"eq", "ne", "notin"}:
        return ValidationImplementationKind.EXPRESSION_CHECK
    if constraint in {"str_contains", "str_startswith", "str_endswith"}:
        return (
            ValidationImplementationKind.EXPRESSION_CHECK
            if field_type in _STRING_TYPES
            else ValidationImplementationKind.UNSUPPORTED
        )
    if constraint == "enum_weights":
        return ValidationImplementationKind.METADATA_ONLY
    return ValidationImplementationKind.UNSUPPORTED


VALIDATION_IMPLEMENTATION_REGISTRY: Mapping[
    tuple[UniversalType, str], ValidationImplementationKind
] = MappingProxyType(
    {
        (field_type, constraint.name): _implementation_kind(field_type, constraint.name)
        for field_type in UniversalType
        for constraint in dataclass_fields(FieldConstraints)
    }
)
@dataclass(frozen=True)
class TableSchemaIssue:
    """One declaration error with a stable pointer and machine-readable code."""
    path: str
    code: str
    message: str
    cause: TypeSpecError = dataclass_field(compare=False)


def _issue(
    issues: list[TableSchemaIssue],
    *,
    path: str,
    code: str,
    cause: TypeSpecError,
) -> None:
    issues.append(TableSchemaIssue(path=path, code=code, message=str(cause), cause=cause))


def _constraint_issue(
    issues: list[TableSchemaIssue], path: str, message: str
) -> None:
    _issue(
        issues,
        path=path,
        code="typespec.invalid_constraint_declaration",
        cause=InvalidConstraintDeclaration(message),
    )


def _validate_constraints(
    definition: FieldDefinition, path: str, issues: list[TableSchemaIssue]
) -> None:
    constraints = definition.constraints
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

    for constraint in dataclass_fields(FieldConstraints):
        name = constraint.name
        value = getattr(constraints, name)
        kind = VALIDATION_IMPLEMENTATION_REGISTRY.get(
            (definition.type, name), ValidationImplementationKind.UNSUPPORTED
        )
        if value is not None and kind is ValidationImplementationKind.UNSUPPORTED:
            type_name = getattr(definition.type, "value", repr(definition.type))
            _constraint_issue(
                issues,
                f"{path}/constraints/{name}",
                f"{name} is not valid for {type_name!r}",
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
        if not isinstance(constraints.enum, (list, tuple)) or not constraints.enum:
            _constraint_issue(issues, f"{path}/constraints/enum", "enum must be a non-empty list")

    if constraints.notin is not None:
        if not isinstance(constraints.notin, (list, tuple)) or not constraints.notin:
            _constraint_issue(issues, f"{path}/constraints/notin", "notin must be a non-empty list")

    for name in ("str_contains", "str_startswith", "str_endswith"):
        value = getattr(constraints, name)
        if value is not None and not isinstance(value, str):
            _constraint_issue(issues, f"{path}/constraints/{name}", f"{name} must be text")

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


def _validate_missing_values(values: Any, path: str, issues: list[TableSchemaIssue]) -> None:
    if values is None:
        return
    if not isinstance(values, (list, tuple)):
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
    definition: FieldDefinition, path: str, issues: list[TableSchemaIssue]
) -> None:
    if not isinstance(definition.format, str) or not definition.format:
        _constraint_issue(issues, f"{path}/format", "format must be a non-empty string")
    elif definition.format.startswith("fmt:"):
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
        if definition.type in allowed_formats:
            if definition.format not in allowed_formats[definition.type] and not (
                definition.type in {UniversalType.DATE, UniversalType.TIME, UniversalType.DATETIME}
                and definition.format
            ):
                _constraint_issue(
                    issues,
                    f"{path}/format",
                    f"format {definition.format!r} is not valid for {definition.type.value!r}",
                )
        elif definition.format != "default":
            _constraint_issue(
                issues,
                f"{path}/format",
                f"{definition.type.value!r} has no format variants",
            )

    if definition.item_type is not None:
        allowed_item_types = {
            UniversalType.STRING.value,
            UniversalType.INTEGER.value,
            UniversalType.NUMBER.value,
            UniversalType.BOOLEAN.value,
            UniversalType.DATE.value,
            UniversalType.TIME.value,
            UniversalType.DATETIME.value,
        }
        if definition.item_type not in allowed_item_types:
            _constraint_issue(
                issues,
                f"{path}/item_type",
                "item_type must be one of the supported primitive list item types",
            )
    if definition.delimiter is not None and (
        not isinstance(definition.delimiter, str) or not definition.delimiter
    ):
        _constraint_issue(issues, f"{path}/delimiter", "delimiter must be a non-empty string")
    _validate_missing_values(definition.missing_values, f"{path}/missing_values", issues)

    if definition.decimal_char is not None and definition.type is not UniversalType.NUMBER:
        _constraint_issue(
            issues,
            f"{path}/decimal_char",
            "decimal_char is valid only for number fields",
        )
    if definition.group_char is not None and definition.type not in {
        UniversalType.INTEGER,
        UniversalType.NUMBER,
    }:
        _constraint_issue(
            issues,
            f"{path}/group_char",
            "group_char is valid only for integer and number fields",
        )
    if definition.bare_number is not None and definition.type not in {
        UniversalType.INTEGER,
        UniversalType.NUMBER,
    }:
        _constraint_issue(
            issues,
            f"{path}/bare_number",
            "bare_number is valid only for integer and number fields",
        )

    if definition.type is not UniversalType.BOOLEAN and (
        definition.true_values is not None or definition.false_values is not None
    ):
        _constraint_issue(
            issues,
            path,
            "true_values and false_values are valid only for boolean fields",
        )
    boolean_values: dict[str, set[str]] = {}
    for property_name in ("true_values", "false_values"):
        values = getattr(definition, property_name)
        if values is None:
            continue
        property_path = f"{path}/{property_name}"
        if not isinstance(values, (list, tuple)) or not values or any(
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

    if definition.categories is not None:
        if definition.type not in {UniversalType.STRING, UniversalType.INTEGER}:
            _constraint_issue(
                issues,
                f"{path}/categories",
                "categories are valid only for string and integer fields",
            )
        elif not isinstance(definition.categories, (list, tuple)):
            _constraint_issue(issues, f"{path}/categories", "categories must be a list")
        else:
            seen_categories: set[tuple[type[Any], Any]] = set()
            labels: set[str] = set()
            for index, category in enumerate(definition.categories):
                category_path = f"{path}/categories/{index}"
                value = category.value if isinstance(category, LabeledValue) else category
                label = category.label if isinstance(category, LabeledValue) else None
                if type(value) is not (
                    str if definition.type is UniversalType.STRING else int
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
    if definition.categories_ordered is not None:
        if definition.categories is None:
            _constraint_issue(
                issues,
                f"{path}/categories_ordered",
                "categories_ordered requires categories",
            )
        elif type(definition.categories_ordered) is not bool:  # noqa: E721 — strict declaration shape
            _constraint_issue(
                issues,
                f"{path}/categories_ordered",
                "categories_ordered must be bool",
            )


def _validate_definition(
    definition: FieldDefinition, path: str, issues: list[TableSchemaIssue]
) -> None:
    """Validate one unnamed declaration, then its nested members and element."""
    if definition.rename_from is not None and (
        not isinstance(definition.rename_from, str) or not definition.rename_from
    ):
        _issue(
            issues,
            path=f"{path}/rename_from",
            code="typespec.invalid_field_identifier",
            cause=InvalidFieldIdentifier(path, "rename_from", definition.rename_from),
        )

    _validate_constraints(definition, path, issues)
    _validate_field_properties(definition, path, issues)

    members = definition.fields
    if isinstance(members, Mapping):
        _validate_field_mapping(
            members, path=f"{path}/fields", issues=issues, allow_empty=True
        )
    elif members is not None and members is not SchemaTypeStatus.UNKNOWN:
        _constraint_issue(
            issues, f"{path}/fields", "fields must be a mapping of FieldDefinition or UNKNOWN"
        )
    element = definition.element
    if isinstance(element, FieldDefinition):
        _validate_definition(element, f"{path}/element", issues)
    elif element is not None and element is not SchemaTypeStatus.UNKNOWN:
        _constraint_issue(
            issues, f"{path}/element", "element must be a FieldDefinition or UNKNOWN"
        )


def _validate_field_mapping(
    fields: Any,
    *,
    path: str,
    issues: list[TableSchemaIssue],
    allow_empty: bool = False,
) -> set[str]:
    """Validate an ordered name→definition mapping; pointers use member position.

    An empty nested record is a declared (empty) structure, distinct from an
    unknown one, so only the top-level schema requires at least one field.
    """
    if not isinstance(fields, Mapping):
        _constraint_issue(issues, path, "fields must be a mapping of name to FieldDefinition")
        return set()
    if not fields and not allow_empty:
        _constraint_issue(issues, path, "fields must be a non-empty mapping of name to FieldDefinition")
        return set()

    names: set[str] = set()
    for index, (name, definition) in enumerate(fields.items()):
        field_path = f"{path}/{index}"
        if not isinstance(name, str) or not name:
            _issue(
                issues,
                path=f"{field_path}/name",
                code="typespec.invalid_field_identifier",
                cause=InvalidFieldIdentifier(field_path, "name", name),
            )
        else:
            names.add(name)
        if not isinstance(definition, FieldDefinition):
            _constraint_issue(issues, field_path, "field must be FieldDefinition")
            continue
        _validate_definition(definition, field_path, issues)
    return names


def _validate_key(
    key: Any, *, path: str, known_names: set[str], issues: list[TableSchemaIssue]
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
    schema: TableSchema,
    *,
    resource_name: str | None,
    package_resource_names: frozenset[str] | None,
    package_schemas: Mapping[str, TableSchema] | None,
    known_names: set[str],
    issues: list[TableSchemaIssue],
) -> None:
    foreign_keys = schema.foreign_keys
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
        target_schema = (
            package_schemas.get(target)
            if package_schemas is not None and target is not None
            else schema
            if target == resource_name
            else None
        )
        if target_schema is not None:
            target_names = {name for name in target_schema.fields if isinstance(name, str)}
            _validate_key(reference.fields, path=f"{path}/reference/fields", known_names=target_names, issues=issues)


def validate_table_schema_semantics(
    schema: TableSchema,
    *,
    resource_name: str | None = None,
    package_resource_names: frozenset[str] | None = None,
    package_schemas: Mapping[str, TableSchema] | None = None,
) -> tuple[TableSchemaIssue, ...]:
    """Return all semantic declaration issues in deterministic pointer order."""
    issues: list[TableSchemaIssue] = []
    known_names = _validate_field_mapping(schema.fields, path="/fields", issues=issues)
    _validate_missing_values(schema.missing_values, "/missing_values", issues)

    if schema.fields_match not in {"exact", "equal", "subset", "superset", "partial", "open"}:
        _constraint_issue(issues, "/fields_match", "fields_match is not a supported mode")
    if schema.primary_key is not None:
        _validate_key(schema.primary_key, path="/primary_key", known_names=known_names, issues=issues)
    if schema.unique_keys is not None:
        if not isinstance(schema.unique_keys, list) or not schema.unique_keys:
            _constraint_issue(issues, "/unique_keys", "unique_keys must be a non-empty list")
        else:
            for index, key in enumerate(schema.unique_keys):
                _validate_key(key, path=f"/unique_keys/{index}", known_names=known_names, issues=issues)
    if package_resource_names is not None and package_schemas is not None:
        _validate_relationships(
            schema,
            resource_name=resource_name,
            package_resource_names=package_resource_names,
            package_schemas=package_schemas,
            known_names=known_names,
            issues=issues,
        )
    elif schema.foreign_keys is not None:
        _validate_relationships(
            schema,
            resource_name=resource_name,
            package_resource_names=None,
            package_schemas=None,
            known_names=known_names,
            issues=issues,
        )
    return tuple(sorted(issues, key=lambda issue: (issue.path, issue.code)))


def require_valid_table_schema(
    schema: TableSchema,
    *,
    resource_name: str | None = None,
    package_resource_names: frozenset[str] | None = None,
    package_schemas: Mapping[str, TableSchema] | None = None,
) -> None:
    """Raise one aggregate error before a declared schema can execute."""
    issues = validate_table_schema_semantics(
        schema,
        resource_name=resource_name,
        package_resource_names=package_resource_names,
        package_schemas=package_schemas,
    )
    if issues:
        raise InvalidTypeSpecSemantics(issues, resource_name)


__all__ = [
    "TableSchemaIssue",
    "require_valid_table_schema",
    "validate_table_schema_semantics",
]
