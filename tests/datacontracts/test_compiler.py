"""Immutable TypeSpec-to-validation-plan compilation."""

import pytest

from mountainash.datacontracts.compiler import compile_datacontract, contract_from_typespec
from mountainash.exceptions import InvalidTypeSpecSemantics
from mountainash.typespec import FieldConstraints, FieldSpec, ForeignKey, ForeignKeyReference, TypeSpec, UniversalType
from mountainash.validation import CompiledValidationPlan, ValueRule, ValueValidatorKey


def test_compiled_plan_snapshots_ordered_nested_definitions_and_relationships():
    child = FieldSpec(type=UniversalType.STRING)
    payload = FieldSpec(fields={"child": child})
    spec = TypeSpec(
        fields={"payload": payload, "amount": FieldSpec(type=UniversalType.INTEGER)},
        foreign_keys=[ForeignKey(
            fields=["payload"],
            reference=ForeignKeyReference(resource=None, fields=["payload"]),
        )],
    )
    plan = compile_datacontract(spec)
    check_ids = tuple(check.id for check in plan.checks)
    spec.fields["later"] = FieldSpec(type=UniversalType.STRING)
    spec.foreign_keys[0].reference.fields.append("other")
    assert isinstance(plan, CompiledValidationPlan)
    assert tuple(check.id for check in plan.checks) == check_ids
    assert tuple(plan.field_plan.by_name) == ("payload", "amount")


def test_compile_datacontract_rejects_semantics_before_compilation():
    spec = TypeSpec(fields={"value": FieldSpec(type=UniversalType.STRING, pattern="[")})
    with pytest.raises(InvalidTypeSpecSemantics):
        compile_datacontract(spec)


def test_generated_contract_retains_definition_constraints_and_severity():
    definition = FieldSpec(
        type=UniversalType.INTEGER,
        eq=1,
        ne=2,
        exclusive_minimum=0,
        exclusive_maximum=3,
        notin=[-1],
        severity="warning",
    )
    contract = contract_from_typespec(TypeSpec(fields={"value": definition}))
    assert contract._contract_fields["value"] is definition
    checks = {check.id: check for check in contract.to_checks()}
    assert {"value__eq", "value__ne", "value__notin", "value_range"} <= set(checks)
    assert all(check.severity == "warning" for check in checks.values())


def test_every_declared_field_gets_type_format_first():
    plan = compile_datacontract(TypeSpec(fields={
        "id": FieldSpec(type=UniversalType.INTEGER),
        "label": FieldSpec(type=UniversalType.STRING, min_length=1, max_length=8),
    }))
    value_rules = [check for check in plan.checks if isinstance(check, ValueRule)]
    assert [(check.id, check.validator) for check in value_rules[:2]] == [
        ("id_type_format", ValueValidatorKey.TYPE_FORMAT),
        ("label_type_format", ValueValidatorKey.TYPE_FORMAT),
    ]


def test_compiler_maps_standard_and_composed_requirements_once():
    plan = compile_datacontract(TypeSpec(fields={
        "amount": FieldSpec(type=UniversalType.NUMBER, constraints=FieldConstraints(
            required=True, unique=True, minimum=1, maximum=10,
            exclusive_minimum=0, exclusive_maximum=11, enum=[1, 2],
            enum_weights={"1": 1.0},
        )),
        "label": FieldSpec(type=UniversalType.STRING, min_length=1, max_length=8,
                           pattern=r"[a-z]+", enum=["draft"], categories=["draft"]),
        "payload": FieldSpec(fields={"child": FieldSpec(type=UniversalType.STRING)},
                             constraints=FieldConstraints(json_schema={"type": "object"})),
        "items": FieldSpec(element=FieldSpec(type=UniversalType.STRING)),
        "shape": FieldSpec(type=UniversalType.GEOJSON),
    }))
    assert [(check.id, check.validator) for check in plan.checks if isinstance(check, ValueRule)] == [
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
        "minimum": 1, "maximum": 10,
        "exclusive_minimum": 0, "exclusive_maximum": 11,
    }
    assert rules["shape_geojson_winding"].severity == "warning"
    assert rules["amount_enum_membership"].metadata["enum_weights"] == {"1": 1.0}
