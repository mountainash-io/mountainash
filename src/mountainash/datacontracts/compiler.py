"""Compile immutable TypeSpec validation plans and native contract classes.

``compile_datacontract(spec)`` returns a ``CompiledValidationPlan`` containing
all local checks and frozen FK declarations. ``contract_from_typespec(spec)``
builds the native declaration class. The standard constraint mapping remains
private to this compiler so callers cannot bypass frozen-plan compilation.
"""
from __future__ import annotations

import datetime
import operator
from functools import reduce
from typing import TYPE_CHECKING, Any

import mountainash as ma
from mountainash.datacontracts.rule import guarded
from mountainash.typespec.spec import FieldConstraints
from mountainash.typespec.converters import _collection_item
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.checks import RelationRule, RowRule, ValueRule, ValueValidatorKey
from mountainash.validation.plan import build_compiled_plan
from mountainash.validation.schema import require_valid_typespec

if TYPE_CHECKING:
    from mountainash.datacontracts.contract import BaseDataContract
    from mountainash.typespec.spec import FieldSpec, TypeSpec
    from mountainash.validation.checks import ValidationCheck
    from mountainash.validation.plan import CompiledValidationPlan
# Truthful Python annotations. DATE/TIME/DATETIME map to their real
# datetime.* types. DURATION/YEAR/YEARMONTH map to str — not a legacy
# stringification defect, but the correct v2 annotation: item 113 Unit B
# (spec §8.2/§11) makes these canonical semantic-string types
# (MountainashDtype.XSD_DURATION/XSD_YEAR/XSD_YEARMONTH), whose physical
# representation is a string on every dtype target (an XSD duration/year/
# yearmonth is a lexical form, e.g. "P3Y6M4DT12H30M5S" / "2024" / "2024-01",
# not a bounded physical int/timedelta — and native string extraction
# cannot prove XML Schema lexical validity). str is therefore the accurate,
# spec-mandated native-contract annotation for these three, matching
# to_canonical()'s boundary mapping (universal_types.py).
UNIVERSAL_TYPE_TO_PYTHON: dict[UniversalType, type] = {
    UniversalType.STRING: str,
    UniversalType.INTEGER: int,
    UniversalType.NUMBER: float,
    UniversalType.BOOLEAN: bool,
    UniversalType.DATE: datetime.date,
    UniversalType.TIME: datetime.time,
    UniversalType.DATETIME: datetime.datetime,
    UniversalType.DURATION: str,
    UniversalType.YEAR: str,
    UniversalType.YEARMONTH: str,
    UniversalType.ANY: object,
}


def _maybe_guard(nullable: bool, col: str, test: Any) -> Any:
    """A null value is not a range/pattern violation; nullability is its own
    check (spec §9.1)."""
    if not nullable:
        return test
    return guarded(precondition=ma.col(col).is_not_null(), test=test)


def _category_values(categories: "list[Any] | None") -> "list[Any] | None":
    if not categories:
        return None
    from mountainash.typespec._categorical import categorical_values
    values = categorical_values(categories)
    return values or None


def _nested_severity_groups(fields: Any, element: Any) -> tuple[str, ...]:
    """List each nested field's explicit severity or the system default."""
    groups: set[str] = set()

    def visit(field: Any) -> None:
        groups.add(field.severity or "blocking")
        if field.fields is not None:
            for child in field.fields.values():
                visit(child)
        if field.element is not None:
            visit(_collection_item(field))

    if fields is not None:
        for child in fields.values():
            visit(child)
    if element is not None:
        visit(element)
    return tuple(sorted(groups)) or ("blocking",)


def constraint_checks(
    field_spec: "FieldSpec",
    local_name: str,
    *,
    severity: str = "blocking",
) -> "list[ValidationCheck]":
    """Compile all standard and extended constraints for one named use."""
    col = local_name
    constraints = field_spec.constraints or FieldConstraints()
    checks: list[ValidationCheck] = [
        ValueRule(
            id=f"{col}_type_format",
            fields=(col,),
            validator=ValueValidatorKey.TYPE_FORMAT,
            options={"type": field_spec.type.value, "format": field_spec.format},
            severity=severity,
        )
    ]
    if constraints.required:
        checks.append(RowRule(
            id=f"{col}__not_null", expr=ma.col(col).is_not_null(),
            severity=severity, fields=[col],
            metadata={"standard_constraint": "required", "field": col},
        ))
    bounds = {
        name: value for name, value in {
            "minimum": constraints.minimum, "maximum": constraints.maximum,
            "exclusive_minimum": constraints.exclusive_minimum,
            "exclusive_maximum": constraints.exclusive_maximum,
        }.items() if value is not None
    }
    if bounds:
        checks.append(ValueRule(id=f"{col}_range", fields=(col,),
            validator=ValueValidatorKey.RANGE, options=bounds, severity=severity))
    lengths = {name: value for name, value in {
        "min_length": constraints.min_length, "max_length": constraints.max_length,
    }.items() if value is not None}
    if lengths:
        checks.append(ValueRule(id=f"{col}_length", fields=(col,),
            validator=ValueValidatorKey.LENGTH, options=lengths, severity=severity))
    if field_spec.type is UniversalType.STRING and field_spec.format != "default":
        checks.append(ValueRule(id=f"{col}_string_format", fields=(col,),
            validator=ValueValidatorKey.STRING_FORMAT,
            options={"format": field_spec.format}, severity=severity))
    if constraints.pattern is not None:
        checks.append(ValueRule(id=f"{col}_pattern", fields=(col,),
            validator=ValueValidatorKey.XSD_PATTERN,
            options={"pattern": constraints.pattern}, severity=severity))
    if constraints.enum is not None:
        checks.append(ValueRule(id=f"{col}_enum_membership", fields=(col,),
            validator=ValueValidatorKey.MEMBERSHIP,
            options={"allowed": constraints.enum}, severity=severity,
            metadata={"enum_weights": constraints.enum_weights}))
    categories = _category_values(field_spec.categories)
    if categories is not None:
        checks.append(ValueRule(id=f"{col}_category_membership", fields=(col,),
            validator=ValueValidatorKey.MEMBERSHIP,
            options={"allowed": categories}, severity=severity))
    if constraints.unique:
        checks.append(ValueRule(id=f"{col}_unique", fields=(col,),
            validator=ValueValidatorKey.UNIQUE, options={}, severity=severity))
    if constraints.json_schema is not None:
        checks.append(ValueRule(id=f"{col}_json_schema", fields=(col,),
            validator=ValueValidatorKey.JSON_SCHEMA,
            options={"schema": constraints.json_schema}, severity=severity))
    extended = (
        ("eq", constraints.eq, lambda value: ma.col(col).eq(value)),
        ("ne", constraints.ne, lambda value: ma.col(col).ne(value)),
        ("notin", constraints.notin, lambda value: ma.col(col).is_in(list(value)).not_()),
        ("str_contains", constraints.str_contains, lambda value: ma.col(col).str.contains(value)),
        ("str_startswith", constraints.str_startswith, lambda value: ma.col(col).str.starts_with(value)),
        ("str_endswith", constraints.str_endswith, lambda value: ma.col(col).str.ends_with(value)),
    )
    for name, value, expression in extended:
        if value is not None:
            checks.append(RowRule(
                id=f"{col}__{name}", expr=_maybe_guard(not constraints.required, col, expression(value)),
                severity=severity, fields=[col],
            ))
    if field_spec.fields is not None or field_spec.element is not None:
        nested_fields = field_spec.fields
        nested_element = _collection_item(field_spec)
        for nested_severity in _nested_severity_groups(
            nested_fields, nested_element
        ):
            suffix = "" if nested_severity == "blocking" else f"__{nested_severity}"
            checks.append(ValueRule(
                id=f"{col}_nested{suffix}",
                fields=(col,),
                validator=ValueValidatorKey.NESTED,
                options={
                    "fields": nested_fields,
                    "element": nested_element,
                    "severity_group": nested_severity,
                },
                severity=nested_severity,
            ))
    if field_spec.type is UniversalType.GEOJSON:
        if field_spec.format == "topojson":
            checks.append(ValueRule(id=f"{col}_topojson", fields=(col,),
                validator=ValueValidatorKey.TOPOJSON, options={}, severity=severity))
        else:
            checks.append(ValueRule(id=f"{col}_geojson", fields=(col,),
                validator=ValueValidatorKey.GEOJSON,
                options={"format": field_spec.format}, severity=severity))
            checks.append(ValueRule(id=f"{col}_geojson_winding", fields=(col,),
                validator=ValueValidatorKey.GEOJSON_WINDING, options={}, severity="warning"))
    return checks


def primary_key_check(spec: "TypeSpec") -> "RelationRule | None":
    """Composite-uniqueness check from TypeSpec.primary_key (spec §9.3 third
    amendment) — a validation OUTCOME reported as a CheckSummary, independent
    of the §7 identity precondition (which raises)."""
    if not spec.primary_key:
        return None
    keys = list(spec.primary_key)

    def plan(rel: Any, _keys: "tuple[str, ...]" = tuple(keys)) -> Any:
        return (
            rel.group_by(*_keys)
            .agg(ma.count_records().alias("__ma_n__"))
            .filter(ma.col("__ma_n__").gt(1))
        )

    return RelationRule(id="primary_key_unique", plan=plan)


def unique_key_checks(spec: "TypeSpec") -> "list[RelationRule]":
    """Compile each composite unique key with SQL MATCH SIMPLE null semantics."""
    checks: list[RelationRule] = []
    for index, key in enumerate(spec.unique_keys or ()):
        keys = tuple(key)

        def plan(rel: Any, _keys: tuple[str, ...] = keys) -> Any:
            non_null = reduce(
                operator.and_,
                (ma.col(name).is_not_null() for name in _keys),
            )
            return (
                rel.filter(non_null)
                .group_by(*_keys)
                .agg(ma.count_records().alias("__ma_n__"))
                .filter(ma.col("__ma_n__").gt(1))
            )

        checks.append(RelationRule(id=f"unique_key__{index}", plan=plan))
    return checks


def compile_field_checks(
    local_name: str, field_spec: "FieldSpec"
) -> "tuple[ValidationCheck, ...]":
    return tuple(constraint_checks(
        field_spec,
        local_name,
        severity=field_spec.severity or "blocking",
    ))


def compile_datacontract(spec: "TypeSpec") -> "CompiledValidationPlan":
    """Compile a semantically valid TypeSpec into one immutable validation plan."""
    require_valid_typespec(spec)
    checks: list[ValidationCheck] = []
    for local_name, field_spec in spec.fields.items():
        checks.extend(compile_field_checks(local_name, field_spec))
    pk_check = primary_key_check(spec)
    if pk_check is not None:
        checks.append(pk_check)
    checks.extend(unique_key_checks(spec))
    return build_compiled_plan(spec, checks)


def contract_from_typespec(
    spec: "TypeSpec", *, name: str | None = None
) -> "type[BaseDataContract]":
    """Generate a native BaseDataContract subclass sharing field definitions."""
    from mountainash.datacontracts.contract import BaseDataContract

    contract_name = name or spec.title or "CompiledDataContract"
    annotations: dict[str, type] = {}
    namespace: dict[str, Any] = {"__annotations__": annotations}
    for local_name, definition in spec.fields.items():
        annotations[local_name] = UNIVERSAL_TYPE_TO_PYTHON.get(definition.type, object)
        namespace[local_name] = definition
    config_attrs: dict[str, Any] = {"name": contract_name}
    if spec.primary_key:
        config_attrs["primary_key"] = spec.primary_key
    namespace["Config"] = type("Config", (BaseDataContract.Config,), config_attrs)
    namespace["__typespec__"] = spec
    return type(contract_name, (BaseDataContract,), namespace)
