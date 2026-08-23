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
from typing import TYPE_CHECKING, Any

import mountainash as ma
from mountainash.datacontracts.rule import guarded
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.checks import RelationRule, RowRule

if TYPE_CHECKING:
    from mountainash.datacontracts.contract import BaseDataContract
    from mountainash.datacontracts.field import Field
    from mountainash.typespec.spec import FieldConstraints, FieldSpec, TypeSpec
    from mountainash.validation.checks import ValidationCheck

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
    values = [
        cat["value"] if isinstance(cat, dict) and "value" in cat else cat
        for cat in categories
    ]
    return values or None


def constraint_checks(
    col: str,
    constraints: "FieldConstraints | None",
    *,
    categories: "list[Any] | None" = None,
    severity: str = "blocking",
) -> "list[ValidationCheck]":
    checks: "list[ValidationCheck]" = []
    c = constraints
    nullable = not (c.required if c is not None else False)

    if c is not None and c.required:
        checks.append(
            RowRule(id=f"{col}__not_null", expr=ma.col(col).is_not_null(),
                    severity=severity, fields=[col])
        )
    if c is not None and c.minimum is not None:
        checks.append(
            RowRule(
                id=f"{col}__ge",
                expr=_maybe_guard(nullable, col, ma.col(col).ge(c.minimum)),
                severity=severity,
                fields=[col],
            )
        )
    if c is not None and c.maximum is not None:
        checks.append(
            RowRule(
                id=f"{col}__le",
                expr=_maybe_guard(nullable, col, ma.col(col).le(c.maximum)),
                severity=severity,
                fields=[col],
            )
        )
    if c is not None and (c.min_length is not None or c.max_length is not None):
        length = ma.col(col).str.len_chars()
        test = None
        if c.min_length is not None:
            test = length.ge(c.min_length)
        if c.max_length is not None:
            upper = length.le(c.max_length)
            test = upper if test is None else (test & upper)
        checks.append(
            RowRule(
                id=f"{col}__str_length",
                expr=_maybe_guard(nullable, col, test),
                severity=severity,
                fields=[col],
            )
        )
    if c is not None and c.pattern is not None:
        checks.append(
            RowRule(
                id=f"{col}__pattern",
                expr=_maybe_guard(
                    nullable, col, ma.col(col).str.regex_contains(c.pattern)
                ),
                severity=severity,
                fields=[col],
            )
        )

    enum_values = c.enum if (c is not None and c.enum is not None) else _category_values(categories)
    if enum_values:
        checks.append(
            RowRule(
                id=f"{col}__isin",
                expr=_maybe_guard(nullable, col, ma.col(col).is_in(enum_values)),
                severity=severity,
                fields=[col],
            )
        )
    if c is not None and c.unique:
        # Row-level via is_duplicated (PR-A prerequisite): every duplicated
        # row is a failure case, not just a table-level verdict.
        checks.append(
            RowRule(
                id=f"{col}__unique",
                expr=ma.col(col).is_duplicated().not_(),
                severity=severity,
                fields=[col],
            )
        )
    return checks


def extra_field_checks(
    col: str, f: "Field", *, severity: str = "blocking"
) -> "list[ValidationCheck]":
    """Beyond-Frictionless Field kwargs (spec §9.1 third amendment) — each a
    guarded RowRule; FieldConstraints stays structurally Frictionless."""
    nullable = f.nullable
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
    keys = (
        [spec.primary_key] if isinstance(spec.primary_key, str) else list(spec.primary_key)
    )

    def plan(rel: Any, _keys: "tuple[str, ...]" = tuple(keys)) -> Any:
        return (
            rel.group_by(*_keys)
            .agg(ma.count_records().alias("__ma_n__"))
            .filter(ma.col("__ma_n__").gt(1))
        )

    return RelationRule(id="primary_key_unique", plan=plan)


def compile_datacontract(spec: "TypeSpec") -> "list[ValidationCheck]":
    """Compile a TypeSpec's field constraints into validation checks."""
    checks: "list[ValidationCheck]" = []
    for field_spec in spec.fields:
        checks.extend(
            constraint_checks(
                field_spec.name, field_spec.constraints, categories=field_spec.categories
            )
        )
    pk_check = primary_key_check(spec)
    if pk_check is not None:
        checks.append(pk_check)
    return checks


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
    namespace["Config"] = type("Config", (), config_attrs)
    namespace["__typespec__"] = spec  # source spec preserved (conform + identity read it)
    return type(contract_name, (BaseDataContract,), namespace)
