"""Immutable TableSchema-to-validation-plan compilation."""

import pytest

from mountainash.datacontracts.compiler import compile_datacontract, compile_field_checks
from mountainash.exceptions import InvalidTypeSpecSemantics
from mountainash.typespec import (
    FieldConstraints,
    FieldDefinition,
    ForeignKey,
    ForeignKeyReference,
    TableSchema,
    UniversalType,
)
from mountainash.validation import CompiledValidationPlan, ValueRule, ValueValidatorKey


def test_compiled_plan_isolated_from_nested_mutation() -> None:
    """Mutating a declaration after compilation must not alter executable checks."""
    schema = TableSchema(
        fields={
            "payload": FieldDefinition(
                type=UniversalType.OBJECT,
                fields={"child": FieldDefinition(type=UniversalType.STRING)},
            )
        },
        foreign_keys=[
            ForeignKey(
                fields=["payload"],
                reference=ForeignKeyReference(resource=None, fields=["payload"]),
            )
        ],
    )

    plan = compile_datacontract(schema)
    fingerprint = plan.declaration_fingerprint
    check_ids = tuple(check.id for check in plan.checks)

    schema.fields["renamed"] = schema.fields.pop("payload")
    schema.foreign_keys[0].reference.fields.append("other")

    assert isinstance(plan, CompiledValidationPlan)
    assert plan.declaration_fingerprint == fingerprint
    assert tuple(check.id for check in plan.checks) == check_ids
    assert plan.field_plan.by_name["payload"].name == "payload"


def test_compile_datacontract_rejects_semantics_before_compilation() -> None:
    """An executable plan cannot be built from a semantically invalid declaration."""
    schema = TableSchema(fields={"": FieldDefinition(type=UniversalType.STRING)})

    with pytest.raises(InvalidTypeSpecSemantics):
        compile_datacontract(schema)


def test_compilation_preserves_extended_constraints_and_severity() -> None:
    """Dropping a retained requirement during plan compilation would weaken a contract."""
    plan = compile_datacontract(
        TableSchema(
            fields={
                "value": FieldDefinition(
                    type=UniversalType.INTEGER,
                    eq=1,
                    ne=2,
                    exclusive_minimum=0,
                    exclusive_maximum=3,
                    notin=[-1],
                    severity="warning",
                ),
                "text": FieldDefinition(
                    type=UniversalType.STRING,
                    str_contains="1",
                    str_startswith="1",
                    str_endswith="1",
                    severity="warning",
                ),
            }
        )
    )

    checks = {check.id: check for check in plan.checks}
    expected = {
        "value__eq",
        "value__ne",
        "value__notin",
        "value_range",
        "text__str_contains",
        "text__str_startswith",
        "text__str_endswith",
    }
    assert expected <= set(checks)
    assert {checks[check_id].severity for check_id in expected} == {"warning"}
    assert checks["value_range"].options == {"exclusive_minimum": 0, "exclusive_maximum": 3}


def test_constraint_not_valid_for_the_declared_type_fails_before_compilation() -> None:
    """The semantic boundary keeps its per-type constraint dispositions for the new vocabulary."""
    schema = TableSchema(
        fields={"value": FieldDefinition(type=UniversalType.INTEGER, str_contains="1")}
    )

    with pytest.raises(InvalidTypeSpecSemantics):
        compile_datacontract(schema)


def test_compile_field_checks_addresses_the_supplied_local_name() -> None:
    """Definitions are unnamed; the explicit local name selects the column."""
    definition = FieldDefinition(type=UniversalType.INTEGER, required=True, minimum=0)

    checks = compile_field_checks(definition, "qty")

    assert [check.id for check in checks] == ["qty_type_format", "qty__not_null", "qty_range"]
    assert all(tuple(check.fields) == ("qty",) for check in checks)
    assert compile_field_checks(definition, "other")[0].id == "other_type_format"


def test_every_declared_field_gets_type_format_first() -> None:
    """Intrinsic format validation exists even without declared constraints."""
    plan = compile_datacontract(
        TableSchema(
            fields={
                "id": FieldDefinition(type=UniversalType.INTEGER),
                "label": FieldDefinition(
                    type=UniversalType.STRING,
                    constraints=FieldConstraints(min_length=1, max_length=8),
                ),
            }
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
        TableSchema(
            fields={
                "amount": FieldDefinition(
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
                "label": FieldDefinition(
                    type=UniversalType.STRING,
                    constraints=FieldConstraints(
                        min_length=1,
                        max_length=8,
                        pattern=r"[a-z]+",
                        enum=["draft"],
                    ),
                    categories=["draft"],
                ),
                "payload": FieldDefinition(
                    type=UniversalType.OBJECT,
                    fields={"child": FieldDefinition(type=UniversalType.STRING)},
                    constraints=FieldConstraints(json_schema={"type": "object"}),
                ),
                "items": FieldDefinition(
                    type=UniversalType.ARRAY,
                    element=FieldDefinition(
                        type=UniversalType.OBJECT,
                        fields={"child": FieldDefinition(type=UniversalType.STRING)},
                    ),
                ),
                "shape": FieldDefinition(type=UniversalType.GEOJSON),
            }
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
    assert rules["shape_geojson_winding"].severity == "warning"
    assert rules["amount_enum_membership"].metadata["enum_weights"] == {"1": 1.0}


def test_unknown_and_empty_nested_shape_declare_no_nested_check() -> None:
    """Unknown or empty structure declares no member/element requirement to check."""
    from mountainash.core.dtypes import SchemaTypeStatus

    plan = compile_datacontract(
        TableSchema(
            fields={
                "unknown_record": FieldDefinition(
                    type=UniversalType.OBJECT, fields=SchemaTypeStatus.UNKNOWN
                ),
                "empty_record": FieldDefinition(type=UniversalType.OBJECT, fields={}),
                "unknown_items": FieldDefinition(
                    type=UniversalType.ARRAY, element=SchemaTypeStatus.UNKNOWN
                ),
            }
        )
    )

    assert not [check for check in plan.checks if check.id.endswith("_nested")]
