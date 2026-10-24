"""Compile immutable TableSchema validation plans and native contract classes.

``compile_datacontract(schema)`` returns a ``CompiledValidationPlan`` containing
all local checks and frozen FK declarations. ``contract_from_table_schema(schema)``
builds the native declaration class. ``compile_field_checks(definition, name)``
is the one owner of the standard constraint vocabulary, so callers cannot bypass
frozen-plan compilation with a second evaluator.
"""
from __future__ import annotations

import datetime
import operator
from copy import deepcopy
from functools import reduce
from typing import TYPE_CHECKING, Any, Mapping

import mountainash as ma
from mountainash.core.dtypes import SchemaTypeStatus
from mountainash.datacontracts.rule import guarded
from mountainash.typespec.spec import FieldConstraints, FieldDefinition
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.checks import RelationRule, RowRule, ValueRule, ValueValidatorKey
from mountainash.validation.plan import build_compiled_plan
from mountainash.validation.schema import require_valid_table_schema

if TYPE_CHECKING:
    from mountainash.datacontracts.contract import BaseDataContract
    from mountainash.typespec.spec import TableSchema
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


def _declares_nested_shape(definition: FieldDefinition) -> bool:
    """True when the definition declares members or an element to check.

    Unknown shape and an empty record declare nothing beyond the container type.
    """
    members = definition.fields
    if isinstance(members, Mapping) and members:
        return True
    element = definition.element
    return element is not None and element is not SchemaTypeStatus.UNKNOWN


def _nested_severities(definition: FieldDefinition, *, root: bool = True) -> "set[str]":
    """Severities of the requirements nested checking evaluates below ``definition``.

    The root contributes only its container-shape requirement; the GeoJSON winding
    check is always advisory, as it is for a top-level field.
    """
    found = {definition.severity or "blocking"}
    if not root and definition.type is UniversalType.GEOJSON and definition.format != "topojson":
        found.add("warning")
    members = definition.fields
    if isinstance(members, Mapping):
        for child in members.values():
            found |= _nested_severities(child, root=False)
    element = definition.element
    if isinstance(element, FieldDefinition):
        found |= _nested_severities(element, root=False)
    return found


def _nested_unique_targets(
    definition: FieldDefinition, path: "tuple[str | None, ...]" = ()
) -> "list[tuple[tuple[str | None, ...], FieldDefinition]]":
    """Declaration paths below ``definition`` whose member/element declares ``unique``.

    Path segments are literal member names; None marks entering a collection's
    elements. The definition itself is the top-level field's own ``unique``.
    """
    targets: "list[tuple[tuple[str | None, ...], FieldDefinition]]" = []
    children: "list[tuple[str | None, FieldDefinition]]" = []
    if isinstance(definition.fields, Mapping):
        children.extend(definition.fields.items())
    if isinstance(definition.element, FieldDefinition):
        children.append((None, definition.element))
    for segment, child in children:
        child_path = (*path, segment)
        if child.constraints.unique:
            targets.append((child_path, child))
        targets.extend(_nested_unique_targets(child, child_path))
    return targets


def _nested_unique_id(col: str, path: "tuple[str | None, ...]") -> str:
    segments = ("*" if s is None else s.replace("~", "~0").replace("/", "~1") for s in path)
    return f"{col}_nested_unique:/" + "/".join(segments)


def constraint_checks(
    definition: FieldDefinition,
    name: str,
    *,
    severity: str = "blocking",
) -> "list[ValidationCheck]":
    """Compile the standard constraint vocabulary shared by value rules.

    ``required`` remains an expression rule because it operates directly on
    post-conform nulls. Every other standard field constraint is a logical
    ``ValueRule`` and therefore shares canonical parsing/equality across
    backends.
    """
    col = name
    constraints = definition.constraints
    checks: "list[ValidationCheck]" = [
        ValueRule(
            id=f"{col}_type_format",
            fields=(col,),
            validator=ValueValidatorKey.TYPE_FORMAT,
            options={"type": definition.type.value, "format": definition.format},
            severity=severity,
        )
    ]

    if constraints.required:
        checks.append(
            RowRule(
                id=f"{col}__not_null",
                expr=ma.col(col).is_not_null(),
                severity=severity,
                fields=[col],
                metadata={"standard_constraint": "required", "field": col},
            )
        )
    bounds = {
        bound: value
        for bound, value in {
            "minimum": constraints.minimum,
            "maximum": constraints.maximum,
            "exclusive_minimum": constraints.exclusive_minimum,
            "exclusive_maximum": constraints.exclusive_maximum,
        }.items()
        if value is not None
    }
    if bounds:
        checks.append(
            ValueRule(
                id=f"{col}_range",
                fields=(col,),
                validator=ValueValidatorKey.RANGE,
                options=bounds,
                severity=severity,
            )
        )
    lengths = {
        bound: value
        for bound, value in {
            "min_length": constraints.min_length,
            "max_length": constraints.max_length,
        }.items()
        if value is not None
    }
    if lengths:
        checks.append(
            ValueRule(
                id=f"{col}_length",
                fields=(col,),
                validator=ValueValidatorKey.LENGTH,
                options=lengths,
                severity=severity,
            )
        )
    if definition.type is UniversalType.STRING and definition.format != "default":
        checks.append(
            ValueRule(
                id=f"{col}_string_format",
                fields=(col,),
                validator=ValueValidatorKey.STRING_FORMAT,
                options={"format": definition.format},
                severity=severity,
            )
        )
    if constraints.pattern is not None:
        checks.append(
            ValueRule(
                id=f"{col}_pattern",
                fields=(col,),
                validator=ValueValidatorKey.XSD_PATTERN,
                options={"pattern": constraints.pattern},
                severity=severity,
            )
        )
    if constraints.enum is not None:
        checks.append(
            ValueRule(
                id=f"{col}_enum_membership",
                fields=(col,),
                validator=ValueValidatorKey.MEMBERSHIP,
                options={"allowed": constraints.enum},
                severity=severity,
                metadata={"enum_weights": constraints.enum_weights},
            )
        )
    categories = _category_values(definition.categories)
    if categories is not None:
        checks.append(
            ValueRule(
                id=f"{col}_category_membership",
                fields=(col,),
                validator=ValueValidatorKey.MEMBERSHIP,
                options={"allowed": categories},
                severity=severity,
            )
        )
    if constraints.unique:
        checks.append(
            ValueRule(
                id=f"{col}_unique",
                fields=(col,),
                validator=ValueValidatorKey.UNIQUE,
                options={},
                severity=severity,
            )
        )
    if constraints.json_schema is not None:
        checks.append(
            ValueRule(
                id=f"{col}_json_schema",
                fields=(col,),
                validator=ValueValidatorKey.JSON_SCHEMA,
                options={"schema": constraints.json_schema},
                severity=severity,
            )
        )
    if _declares_nested_shape(definition):
        # Member/element requirements answer to their own definition's severity,
        # never the enclosing field's: one rule per severity actually present, the
        # blocking one keeping the established id.
        for nested_severity in ("blocking", "warning"):
            if nested_severity == "blocking" or nested_severity in _nested_severities(definition):
                checks.append(
                    ValueRule(
                        id=f"{col}_nested" + ("" if nested_severity == "blocking" else f"_{nested_severity}"),
                        fields=(col,),
                        validator=ValueValidatorKey.NESTED,
                        options={"definition": definition, "severity": nested_severity},
                        severity=nested_severity,
                    )
                )
    for unique_path, unique_definition in _nested_unique_targets(definition):
        checks.append(
            ValueRule(
                id=_nested_unique_id(col, unique_path),
                fields=(col,),
                validator=ValueValidatorKey.UNIQUE,
                options={"path": unique_path},
                severity=unique_definition.severity or "blocking",
            )
        )
    if definition.type is UniversalType.GEOJSON:
        if definition.format == "topojson":
            checks.append(
                ValueRule(
                    id=f"{col}_topojson",
                    fields=(col,),
                    validator=ValueValidatorKey.TOPOJSON,
                    options={},
                    severity=severity,
                )
            )
        else:
            checks.append(
                ValueRule(
                    id=f"{col}_geojson",
                    fields=(col,),
                    validator=ValueValidatorKey.GEOJSON,
                    options={"format": definition.format},
                    severity=severity,
                )
            )
            checks.append(
                ValueRule(
                    id=f"{col}_geojson_winding",
                    fields=(col,),
                    validator=ValueValidatorKey.GEOJSON_WINDING,
                    options={},
                    severity="warning",
                )
            )
    return checks


def comparison_checks(
    constraints: FieldConstraints,
    name: str,
    *,
    severity: str = "blocking",
) -> "list[ValidationCheck]":
    """Compile equality/exclusion/string constraints to guarded row expressions."""
    tests: "list[tuple[str, Any]]" = []
    if constraints.eq is not None:
        tests.append(("eq", ma.col(name).eq(constraints.eq)))
    if constraints.ne is not None:
        tests.append(("ne", ma.col(name).ne(constraints.ne)))
    if constraints.notin is not None:
        tests.append(("notin", ma.col(name).is_in(list(constraints.notin)).not_()))
    if constraints.str_contains is not None:
        tests.append(("str_contains", ma.col(name).str.contains(constraints.str_contains)))
    if constraints.str_startswith is not None:
        tests.append(("str_startswith", ma.col(name).str.starts_with(constraints.str_startswith)))
    if constraints.str_endswith is not None:
        tests.append(("str_endswith", ma.col(name).str.ends_with(constraints.str_endswith)))
    return [
        RowRule(
            id=f"{name}__{check}",
            expr=_maybe_guard(not constraints.required, name, test),
            severity=severity,
            fields=[name],
        )
        for check, test in tests
    ]


def primary_key_check(schema: "TableSchema") -> "RelationRule | None":
    """Composite-uniqueness check from TableSchema.primary_key (spec §9.3 third
    amendment) — a validation OUTCOME reported as a CheckSummary, independent
    of the §7 identity precondition (which raises)."""
    if not schema.primary_key:
        return None
    keys = list(schema.primary_key)

    def plan(rel: Any, _keys: "tuple[str, ...]" = tuple(keys)) -> Any:
        return (
            rel.group_by(*_keys)
            .agg(ma.count_records().alias("__ma_n__"))
            .filter(ma.col("__ma_n__").gt(1))
        )

    return RelationRule(id="primary_key_unique", plan=plan)


def unique_key_checks(schema: "TableSchema") -> "list[RelationRule]":
    """Compile each composite unique key with SQL MATCH SIMPLE null semantics."""
    checks: list[RelationRule] = []
    for index, key in enumerate(schema.unique_keys or ()):
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
    definition: FieldDefinition,
    name: str,
) -> "tuple[ValidationCheck, ...]":
    """Compile one definition's complete constraint vocabulary for local ``name``.

    The definition is unnamed; ``name`` supplies the column the checks address.
    Severity comes from the definition, otherwise the system default.
    """
    severity = definition.severity or "blocking"
    return (
        *constraint_checks(definition, name, severity=severity),
        *comparison_checks(definition.constraints, name, severity=severity),
    )


def compile_datacontract(schema: "TableSchema") -> "CompiledValidationPlan":
    """Compile a semantically valid TableSchema into one immutable validation plan."""
    require_valid_table_schema(schema)
    checks: "list[ValidationCheck]" = []
    for name, definition in tuple(schema.fields.items()):
        checks.extend(compile_field_checks(definition, name))
    pk_check = primary_key_check(schema)
    if pk_check is not None:
        checks.append(pk_check)
    checks.extend(unique_key_checks(schema))
    return build_compiled_plan(schema, checks)


def contract_from_table_schema(
    schema: "TableSchema", *, name: str | None = None
) -> "type[BaseDataContract]":
    """Generate a native BaseDataContract subclass from a TableSchema.

    Each field becomes an explicit ``FieldDefinition`` member, so the full
    declaration (constraints, severity, source binding, nested shape) survives
    the schema↔contract round trip.
    """
    from mountainash.datacontracts.contract import BaseDataContract

    contract_name = name or schema.title or "CompiledDataContract"
    annotations: dict[str, type] = {}
    namespace: dict[str, Any] = {"__annotations__": annotations}
    for field_name, definition in schema.fields.items():
        annotations[field_name] = UNIVERSAL_TYPE_TO_PYTHON.get(definition.type, object)
        namespace[field_name] = definition
    config_attrs: dict[str, Any] = {"name": contract_name}
    if schema.primary_key:
        config_attrs["primary_key"] = schema.primary_key
    namespace["Config"] = type("Config", (BaseDataContract.Config,), config_attrs)
    namespace["__table_schema__"] = deepcopy(schema)  # source schema preserved (conform + identity read it)
    return type(contract_name, (BaseDataContract,), namespace)
