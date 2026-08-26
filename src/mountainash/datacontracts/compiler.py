"""Compile TypeSpec constraints into validation checks + native contract classes.

compile_datacontract(spec) -> list[ValidationCheck]   (intra-table checks ONLY;
    TypeSpec.foreign_keys are owned by mountainash.validation.fk.build_fk_checks;
    TypeSpec.primary_key ALSO emits the composite-uniqueness RelationRule here)
contract_from_typespec(spec) -> type[BaseDataContract] (the class factory)
constraint_checks(col, constraints)                    (the ONE constraint->check mapping)
extra_field_checks(col, field)                         (beyond-Frictionless Field kwargs)
"""
from __future__ import annotations

import datetime
import operator
from functools import reduce
from typing import TYPE_CHECKING, Any, Mapping

import mountainash as ma
from mountainash.datacontracts.rule import guarded
from mountainash.typespec.spec import FieldConstraints
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.checks import RelationRule, RowRule, ValueRule, ValueValidatorKey
from mountainash.validation.plan import (
    build_compiled_plan,
    freeze_field_extension,
)
from mountainash.validation.schema import require_valid_typespec

if TYPE_CHECKING:
    from mountainash.datacontracts.contract import BaseDataContract
    from mountainash.datacontracts.field import Field
    from mountainash.validation.plan import FieldValidationExtension
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


def constraint_checks(
    field_spec: "FieldSpec",
    *,
    severity: str = "blocking",
) -> "list[ValidationCheck]":
    """Compile the complete standard constraint vocabulary once.

    ``required`` remains an expression rule because it operates directly on
    post-conform nulls. Every other standard field constraint is a logical
    ``ValueRule`` and therefore shares canonical parsing/equality across
    backends.
    """
    col = field_spec.name
    constraints = field_spec.constraints
    checks: "list[ValidationCheck]" = [
        ValueRule(
            id=f"{col}_type_format",
            fields=(col,),
            validator=ValueValidatorKey.TYPE_FORMAT,
            options={"type": field_spec.type.value, "format": field_spec.format},
            severity=severity,
        )
    ]
    constraints = constraints or FieldConstraints()

    if constraints.required:
        checks.append(
            RowRule(
                id=f"{col}__not_null",
                expr=ma.col(col).is_not_null(),
                severity=severity,
                fields=[col],
            )
        )
    bounds = {
        name: value
        for name, value in {
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
        name: value
        for name, value in {
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
    if field_spec.type is UniversalType.STRING and field_spec.format != "default":
        checks.append(
            ValueRule(
                id=f"{col}_string_format",
                fields=(col,),
                validator=ValueValidatorKey.STRING_FORMAT,
                options={"format": field_spec.format},
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
    categories = _category_values(field_spec.categories)
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
    if field_spec.object_fields or field_spec.item_object_fields:
        checks.append(
            ValueRule(
                id=f"{col}_nested",
                fields=(col,),
                validator=ValueValidatorKey.NESTED,
                options={
                    "object_fields": field_spec.object_fields,
                    "item_object_fields": field_spec.item_object_fields,
                },
                severity=severity,
            )
        )
    if field_spec.type is UniversalType.GEOJSON:
        if field_spec.format == "topojson":
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
                    options={"format": field_spec.format},
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

def extra_field_checks(
    col: str,
    f: Any,
    *,
    severity: str = "blocking",
    nullable: bool | None = None,
) -> "list[ValidationCheck]":
    """Compile native Field additions outside the Frictionless constraint shape."""
    nullable = f.nullable if nullable is None else nullable
    tests: "list[tuple[str, Any]]" = []
    if f.eq is not None:
        tests.append(("eq", ma.col(col).eq(f.eq)))
    if f.ne is not None:
        tests.append(("ne", ma.col(col).ne(f.ne)))
    if f.gt is not None:
        tests.append(("gt", ma.col(col).gt(f.gt)))
    if f.lt is not None:
        tests.append(("lt", ma.col(col).lt(f.lt)))
    if f.notin is not None:
        tests.append(("notin", ma.col(col).is_in(list(f.notin)).not_()))
    if f.str_contains is not None:
        tests.append(("str_contains", ma.col(col).str.contains(f.str_contains)))
    if f.str_startswith is not None:
        tests.append(("str_startswith", ma.col(col).str.starts_with(f.str_startswith)))
    if f.str_endswith is not None:
        tests.append(("str_endswith", ma.col(col).str.ends_with(f.str_endswith)))
    return [
        RowRule(
            id=f"{col}__{name}",
            expr=_maybe_guard(nullable, col, test),
            severity=severity,
            fields=[col],
        )
        for name, test in tests
    ]


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
    field_spec: "FieldSpec",
    *,
    extension: "FieldValidationExtension | None" = None,
) -> "tuple[ValidationCheck, ...]":
    """Compile one standard field plus its frozen native additions."""
    severity = extension.severity if extension is not None else "blocking"
    checks = constraint_checks(field_spec, severity=severity)
    if extension is not None:
        checks.extend(
            extra_field_checks(
                field_spec.name,
                extension,
                severity=extension.severity,
                nullable=not (
                    field_spec.constraints.required
                    if field_spec.constraints is not None
                    else False
                ),
            )
        )
    return tuple(checks)


def compile_datacontract(
    spec: "TypeSpec",
    extensions: "Mapping[str, Field] | None" = None,
) -> "CompiledValidationPlan":
    """Compile a semantically valid TypeSpec into one immutable validation plan."""
    require_valid_typespec(spec)
    extensions = extensions or {}
    unknown_extensions = set(extensions) - set(spec.field_names)
    if unknown_extensions:
        raise ValueError(
            f"native extensions name undeclared fields: {sorted(unknown_extensions)!r}"
        )
    frozen_extensions = {
        name: freeze_field_extension(field) for name, field in extensions.items()
    }
    checks: "list[ValidationCheck]" = []
    for field_spec in spec.fields:
        checks.extend(
            compile_field_checks(
                field_spec,
                extension=frozen_extensions.get(field_spec.name),
            )
        )
    pk_check = primary_key_check(spec)
    if pk_check is not None:
        checks.append(pk_check)
    checks.extend(unique_key_checks(spec))
    return build_compiled_plan(spec, checks)


def _field_from_spec(field_spec: "FieldSpec") -> "Field":
    from mountainash.datacontracts.field import Field

    c = field_spec.constraints
    enum = None
    if c is not None and c.enum is not None:
        enum = list(c.enum)
    else:
        enum = _category_values(field_spec.categories)
    if c is None:
        return Field(isin=enum, title=field_spec.title, description=field_spec.description)
    str_length: "dict[str, int] | None" = None
    if c.min_length is not None or c.max_length is not None:
        str_length = {}
        if c.min_length is not None:
            str_length["min_value"] = c.min_length
        if c.max_length is not None:
            str_length["max_value"] = c.max_length
    return Field(
        nullable=not c.required,
        ge=c.minimum,
        le=c.maximum,
        isin=enum,
        str_matches=c.pattern,
        str_length=str_length,
        unique=c.unique,
        title=field_spec.title,
        description=field_spec.description,
    )


def contract_from_typespec(
    spec: "TypeSpec", *, name: str | None = None
) -> "type[BaseDataContract]":
    """Generate a native BaseDataContract subclass from a TypeSpec."""
    from mountainash.datacontracts.contract import BaseDataContract

    contract_name = name or spec.title or "CompiledDataContract"
    annotations: dict[str, type] = {}
    namespace: dict[str, Any] = {"__annotations__": annotations}
    for field_spec in spec.fields:
        annotations[field_spec.name] = UNIVERSAL_TYPE_TO_PYTHON.get(field_spec.type, object)
        namespace[field_spec.name] = _field_from_spec(field_spec)
    config_attrs: dict[str, Any] = {"name": contract_name}
    if spec.primary_key:
        config_attrs["primary_key"] = spec.primary_key
    namespace["Config"] = type("Config", (BaseDataContract.Config,), config_attrs)
    namespace["__typespec__"] = spec  # source spec preserved (conform + identity read it)
    return type(contract_name, (BaseDataContract,), namespace)
