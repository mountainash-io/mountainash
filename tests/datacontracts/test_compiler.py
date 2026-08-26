"""Immutable TypeSpec-to-validation-plan compilation."""

import pytest

from mountainash.datacontracts.compiler import compile_datacontract
from mountainash.exceptions import InvalidTypeSpecSemantics
from mountainash.typespec import (
    FieldConstraints,
    FieldSpec,
    ForeignKey,
    ForeignKeyReference,
    TypeSpec,
    UniversalType,
)
from mountainash.validation import CompiledValidationPlan, ValueRule, ValueValidatorKey


def test_compiled_plan_isolated_from_nested_mutation() -> None:
    """Mutating a declaration after compilation must not alter executable checks."""
    spec = TypeSpec(
        fields=[
            FieldSpec(
                name="payload",
                type=UniversalType.OBJECT,
                object_fields=[FieldSpec(name="child", type=UniversalType.STRING)],
            )
        ],
        foreign_keys=[
            ForeignKey(
                fields=["payload"],
                reference=ForeignKeyReference(resource=None, fields=["payload"]),
            )
        ],
    )

    plan = compile_datacontract(spec)
    fingerprint = plan.declaration_fingerprint
    check_ids = tuple(check.id for check in plan.checks)

    spec.fields[0].object_fields[0].name = "renamed"
    spec.foreign_keys[0].reference.fields.append("other")

    assert isinstance(plan, CompiledValidationPlan)
    assert plan.declaration_fingerprint == fingerprint
    assert tuple(check.id for check in plan.checks) == check_ids
    assert plan.field_plan.by_name["payload"].name == "payload"


def test_compile_datacontract_rejects_semantics_before_compilation() -> None:
    """An executable plan cannot be built from a semantically invalid declaration."""
    spec = TypeSpec(fields=[FieldSpec(name="", type=UniversalType.STRING)])

    with pytest.raises(InvalidTypeSpecSemantics):
        compile_datacontract(spec)


def test_compilation_preserves_native_field_extensions_and_severity() -> None:
    """Dropping native rules during plan compilation would weaken a contract."""
    from mountainash.datacontracts import BaseDataContract, Field

    class NativeContract(BaseDataContract):
        value: int = Field(
            eq=1,
            ne=2,
            gt=0,
            lt=3,
            notin=[-1],
            str_contains="1",
            str_startswith="1",
            str_endswith="1",
            severity="warning",
        )

    plan = compile_datacontract(
        NativeContract.to_typespec(),
        extensions=NativeContract._contract_fields,
    )

    checks = {check.id: check for check in plan.checks}
    expected = {
        "value__eq",
        "value__ne",
        "value__gt",
        "value__lt",
        "value__notin",
        "value__str_contains",
        "value__str_startswith",
        "value__str_endswith",
    }
    assert expected <= set(checks)
    assert {checks[check_id].severity for check_id in expected} == {"warning"}



def test_every_declared_field_gets_type_format_first() -> None:
    """Intrinsic format validation exists even without declared constraints."""
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(name="id", type=UniversalType.INTEGER),
                FieldSpec(
                    name="label",
                    type=UniversalType.STRING,
                    constraints=FieldConstraints(min_length=1, max_length=8),
                ),
            ]
        )
    )

    value_rules = [check for check in plan.checks if isinstance(check, ValueRule)]
    assert [
        (check.id, check.validator)
        for check in value_rules[:2]
    ] == [
        ("id_type_format", ValueValidatorKey.TYPE_FORMAT),
        ("label_type_format", ValueValidatorKey.TYPE_FORMAT),
    ]


def test_compiler_maps_each_standard_constraint_once() -> None:
    """The complete standard vocabulary has one explicit ValueRule owner."""
    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(
                    name="amount",
                    type=UniversalType.NUMBER,
                    constraints=FieldConstraints(
                        required=True,
                        unique=True,
                        minimum=1,
                        maximum=10,
                        exclusive_minimum=0,
                        exclusive_maximum=11,
                        enum=[1, 2],
                        enum_weights={"1": 1.0},
                    ),
                ),
                FieldSpec(
                    name="label",
                    type=UniversalType.STRING,
                    constraints=FieldConstraints(
                        min_length=1,
                        max_length=8,
                        pattern=r"[a-z]+",
                        enum=["draft"],
                    ),
                    categories=["draft"],
                ),
                FieldSpec(
                    name="payload",
                    type=UniversalType.OBJECT,
                    object_fields=[FieldSpec(name="child", type=UniversalType.STRING)],
                    constraints=FieldConstraints(json_schema={"type": "object"}),
                ),
                FieldSpec(
                    name="items",
                    type=UniversalType.ARRAY,
                    item_object_fields=[FieldSpec(name="child", type=UniversalType.STRING)],
                ),
                FieldSpec(name="shape", type=UniversalType.GEOJSON),
            ]
        )
    )

    assert [
        (check.id, check.validator)
        for check in plan.checks
        if isinstance(check, ValueRule)
    ] == [
        ("amount_type_format", ValueValidatorKey.TYPE_FORMAT),
        ("amount_range", ValueValidatorKey.RANGE),
        ("amount_enum_membership", ValueValidatorKey.MEMBERSHIP),
        ("amount_unique", ValueValidatorKey.UNIQUE),
        ("label_type_format", ValueValidatorKey.TYPE_FORMAT),
        ("label_length", ValueValidatorKey.LENGTH),
        ("label_pattern", ValueValidatorKey.XSD_PATTERN),
        ("label_enum_membership", ValueValidatorKey.MEMBERSHIP),
        ("label_category_membership", ValueValidatorKey.MEMBERSHIP),
        ("payload_type_format", ValueValidatorKey.TYPE_FORMAT),
        ("payload_json_schema", ValueValidatorKey.JSON_SCHEMA),
        ("payload_nested", ValueValidatorKey.NESTED),
        ("items_type_format", ValueValidatorKey.TYPE_FORMAT),
        ("items_nested", ValueValidatorKey.NESTED),
        ("shape_type_format", ValueValidatorKey.TYPE_FORMAT),
        ("shape_geojson", ValueValidatorKey.GEOJSON),
        ("shape_geojson_winding", ValueValidatorKey.GEOJSON_WINDING),
    ]
    rules = {check.id: check for check in plan.checks}
    assert rules["amount_range"].options == {
        "minimum": 1,
        "maximum": 10,
        "exclusive_minimum": 0,
        "exclusive_maximum": 11,
    }
    assert rules["amount_enum_membership"].metadata["enum_weights"] == {"1": 1.0}
