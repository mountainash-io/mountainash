"""TypeSpec semantic declaration validation."""

import pytest

from mountainash.exceptions import InvalidConstraintDeclaration, InvalidTypeSpecSemantics, TypeSpecError
from mountainash.typespec import (
    FieldConstraints, FieldSpec, ForeignKey, ForeignKeyReference, LabeledValue,
    TypeSpec, UniversalType,
)
from mountainash.validation import require_valid_typespec, validate_typespec_semantics


def test_validation_implementation_registry_is_closed():
    from dataclasses import fields
    from mountainash.validation.schema import VALIDATION_IMPLEMENTATION_REGISTRY, ValidationImplementationKind
    discovered = {
        (field_type, constraint.name)
        for field_type in UniversalType
        for constraint in fields(FieldConstraints)
    }
    assert set(VALIDATION_IMPLEMENTATION_REGISTRY) == discovered
    assert set(VALIDATION_IMPLEMENTATION_REGISTRY.values()) <= set(ValidationImplementationKind)


def test_semantic_issues_are_complete_and_deterministically_ordered():
    spec = TypeSpec(fields={
        "amount": FieldSpec(type=UniversalType.INTEGER,
                            constraints=FieldConstraints(min_length=-1, pattern="[")),
    })
    issues = validate_typespec_semantics(spec)
    assert tuple((issue.path, issue.code) for issue in issues) == tuple(
        sorted((issue.path, issue.code) for issue in issues)
    )
    assert {type(issue.cause) for issue in issues} >= {InvalidConstraintDeclaration}


def test_require_valid_typespec_raises_one_aggregate():
    spec = TypeSpec(fields={"": FieldSpec(type=UniversalType.STRING)})
    with pytest.raises(InvalidTypeSpecSemantics) as caught:
        require_valid_typespec(spec, resource_name="orders")
    assert caught.value.resource_name == "orders"
    assert caught.value.issues == validate_typespec_semantics(spec, resource_name="orders")
    assert isinstance(caught.value, TypeSpecError)


@pytest.mark.parametrize(("field", "path"), [
    (FieldSpec(type=UniversalType.LIST, item_type="object"), "/fields/values/item_type"),
    (FieldSpec(type=UniversalType.INTEGER, constraints=FieldConstraints(min_length=-1)), "/fields/values/constraints/min_length"),
])
def test_semantic_validation_rejects_invalid_programmatic_properties(field, path):
    issues = validate_typespec_semantics(TypeSpec(fields={"values": field}))
    assert any(issue.path == path for issue in issues)


def test_semantic_validation_checks_package_foreign_key_target_fields():
    orders = TypeSpec(
        fields={"customer_id": FieldSpec(type=UniversalType.INTEGER)},
        foreign_keys=[ForeignKey(fields=["customer_id"], reference=ForeignKeyReference(
            resource="customers", fields=["missing"]
        ))],
    )
    customers = TypeSpec(fields={"id": FieldSpec(type=UniversalType.INTEGER)})
    issues = validate_typespec_semantics(
        orders, resource_name="orders",
        package_resource_names=frozenset({"orders", "customers"}),
        package_specs={"orders": orders, "customers": customers},
    )
    assert any(issue.path == "/foreign_keys/0/reference/fields/0" for issue in issues)


def test_semantic_validation_rejects_an_explicitly_empty_foreign_key_list():
    spec = TypeSpec(fields={"id": FieldSpec(type=UniversalType.INTEGER)}, foreign_keys=[])
    assert any(issue.path == "/foreign_keys" for issue in validate_typespec_semantics(spec))


def test_semantic_validation_rejects_invalid_boolean_and_category_declarations():
    spec = TypeSpec(fields={
        "enabled": FieldSpec(type=UniversalType.BOOLEAN,
                              true_values=["yes", "yes"], false_values=["yes"]),
        "status": FieldSpec(type=UniversalType.STRING, categories=[
            LabeledValue("open", "Open"), LabeledValue("open", "Duplicate")
        ]),
        "amount": FieldSpec(type=UniversalType.INTEGER, decimal_char="."),
    })
    paths = {issue.path for issue in validate_typespec_semantics(spec)}
    assert {
        "/fields/enabled/true_values", "/fields/enabled/false_values",
        "/fields/status/categories/1", "/fields/amount/decimal_char",
    } <= paths


def test_semantic_validation_rejects_ambiguous_missing_value_labels():
    spec = TypeSpec(fields={"note": FieldSpec(type=UniversalType.STRING, missing_values=[
        LabeledValue("NA", "Not available"), LabeledValue("NA", "Repeated value"),
    ])}, missing_values=[LabeledValue("NULL", "Missing"), LabeledValue("N/A", "Missing")])
    paths = {issue.path for issue in validate_typespec_semantics(spec)}
    assert {"/fields/note/missing_values/1", "/missing_values/1"} <= paths


@pytest.mark.parametrize("schema", [
    {"$ref": "https://example.test/schema.json"},
    {"$dynamicRef": "https://example.test/schema.json"},
])
def test_semantic_validation_denies_remote_json_schema_references(schema):
    from mountainash.exceptions import JSONSchemaReferenceDenied
    spec = TypeSpec(fields={"payload": FieldSpec(type=UniversalType.OBJECT,
        constraints=FieldConstraints(json_schema=schema))})
    issues = validate_typespec_semantics(spec)
    assert isinstance(issues[0].cause, JSONSchemaReferenceDenied)
