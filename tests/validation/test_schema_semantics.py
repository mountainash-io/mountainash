"""TableSchema semantic declaration validation."""

import pytest

from mountainash.exceptions import (
    InvalidConstraintDeclaration,
    InvalidFieldIdentifier,
    InvalidTypeSpecSemantics,
    TypeSpecError,
)
from mountainash.core.dtypes import SchemaTypeStatus
from mountainash.typespec import (
    FieldConstraints,
    FieldDefinition,
    ForeignKey,
    ForeignKeyReference,
    LabeledValue,
    TableSchema,
    UniversalType,
)
from mountainash.validation import require_valid_table_schema, validate_table_schema_semantics

def test_validation_implementation_registry_is_closed() -> None:
    """An added field constraint needs one explicit disposition for every type."""
    from dataclasses import fields

    from mountainash.validation.schema import (
        VALIDATION_IMPLEMENTATION_REGISTRY,
        ValidationImplementationKind,
    )

    discovered = {
        (field_type, constraint.name)
        for field_type in UniversalType
        for constraint in fields(FieldConstraints)
    }

    assert set(VALIDATION_IMPLEMENTATION_REGISTRY) == discovered
    assert set(VALIDATION_IMPLEMENTATION_REGISTRY.values()) <= set(
        ValidationImplementationKind
    )


def test_semantic_issues_are_complete_and_deterministically_ordered() -> None:
    """Removing deterministic aggregation would hide independent declaration faults."""
    schema = TableSchema(
        fields={
            "": FieldDefinition(type=UniversalType.STRING),
            "amount": FieldDefinition(
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(min_length=-1, pattern="["),
            ),
        }
    )

    issues = validate_table_schema_semantics(schema)

    assert tuple((issue.path, issue.code) for issue in issues) == tuple(
        sorted((issue.path, issue.code) for issue in issues)
    )
    assert {type(issue.cause) for issue in issues} >= {
        InvalidFieldIdentifier,
        InvalidConstraintDeclaration,
    }


def test_require_valid_table_schema_raises_one_aggregate() -> None:
    """Removing the execution boundary must prevent invalid declarations running."""
    schema = TableSchema(fields={"": FieldDefinition(type=UniversalType.STRING)})

    with pytest.raises(InvalidTypeSpecSemantics) as caught:
        require_valid_table_schema(schema, resource_name="orders")

    assert caught.value.resource_name == "orders"
    assert caught.value.issues == validate_table_schema_semantics(
        schema, resource_name="orders"
    )
    assert isinstance(caught.value, TypeSpecError)


def test_empty_top_level_schema_is_rejected() -> None:
    """A schema without any field cannot address a column to check."""
    issues = validate_table_schema_semantics(TableSchema(fields={}))

    assert [issue.path for issue in issues] == ["/fields"]


def test_nested_members_and_element_are_validated_by_position() -> None:
    """Nested declarations get the same semantic checks, pointed at by position."""
    schema = TableSchema(
        fields={
            "record": FieldDefinition(
                type=UniversalType.OBJECT,
                fields={
                    "ok": FieldDefinition(type=UniversalType.STRING),
                    "bad": FieldDefinition(
                        type=UniversalType.STRING,
                        constraints=FieldConstraints(min_length=-1),
                    ),
                    "": FieldDefinition(type=UniversalType.STRING),
                },
            ),
            "items": FieldDefinition(
                type=UniversalType.ARRAY,
                element=FieldDefinition(
                    type=UniversalType.INTEGER,
                    constraints=FieldConstraints(pattern="x"),
                ),
            ),
        }
    )

    paths = {issue.path for issue in validate_table_schema_semantics(schema)}

    assert {
        "/fields/0/fields/1/constraints/min_length",
        "/fields/0/fields/2/name",
        "/fields/1/element/constraints/pattern",
    } <= paths


def test_unknown_and_empty_nested_shape_are_valid_declarations() -> None:
    """Unknown shape and an empty record are distinct, legitimate declarations."""
    schema = TableSchema(
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

    assert validate_table_schema_semantics(schema) == ()


@pytest.mark.parametrize(
    ("constraint", "valid_type"),
    [
        ({"eq": "a"}, UniversalType.STRING),
        ({"ne": 1}, UniversalType.INTEGER),
        ({"notin": [1]}, UniversalType.INTEGER),
        ({"str_contains": "a"}, UniversalType.STRING),
        ({"str_startswith": "a"}, UniversalType.STRING),
        ({"str_endswith": "a"}, UniversalType.STRING),
    ],
)
def test_extended_constraints_have_type_dispositions(constraint, valid_type) -> None:
    """The extended vocabulary is accepted for its types and rejected elsewhere."""
    accepted = TableSchema(fields={"v": FieldDefinition(type=valid_type, **constraint)})
    assert validate_table_schema_semantics(accepted) == ()

    if next(iter(constraint)).startswith("str_"):
        rejected = TableSchema(
            fields={"v": FieldDefinition(type=UniversalType.INTEGER, **constraint)}
        )
        assert validate_table_schema_semantics(rejected)


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (
            lambda definition: object.__setattr__(definition, "format", "fmt:%Y"),
            "/fields/0/format",
        ),
        (
            lambda definition: object.__setattr__(definition, "item_type", "object"),
            "/fields/0/item_type",
        ),
        (
            lambda definition: object.__setattr__(definition.constraints, "required", 1),
            "/fields/0/constraints/required",
        ),
    ],
)
def test_semantic_validation_rechecks_mutated_programmatic_properties(
    mutate, path: str
) -> None:
    """Bypassing dataclass construction must not bypass declaration validation."""
    definition = FieldDefinition(
        type=UniversalType.LIST,
        constraints=FieldConstraints(required=True),
    )
    mutate(definition)

    issues = validate_table_schema_semantics(TableSchema(fields={"values": definition}))

    assert any(issue.path == path for issue in issues)


def test_semantic_validation_checks_package_foreign_key_target_fields() -> None:
    """A typo in a package key target must fail before any resource is read."""
    orders = TableSchema(
        fields={"customer_id": FieldDefinition(type=UniversalType.INTEGER)},
        foreign_keys=[
            ForeignKey(
                fields=["customer_id"],
                reference=ForeignKeyReference(resource="customers", fields=["missing"]),
            )
        ],
    )
    customers = TableSchema(fields={"id": FieldDefinition(type=UniversalType.INTEGER)})

    issues = validate_table_schema_semantics(
        orders,
        resource_name="orders",
        package_resource_names=frozenset({"orders", "customers"}),
        package_schemas={"orders": orders, "customers": customers},
    )
    assert any(issue.path == "/foreign_keys/0/reference/fields/0" for issue in issues)


def test_semantic_validation_rejects_an_explicitly_empty_foreign_key_list() -> None:
    """Treating [] like omission loses an invalid explicit declaration."""
    schema = TableSchema(
        fields={"id": FieldDefinition(type=UniversalType.INTEGER)},
        foreign_keys=[],
    )

    issues = validate_table_schema_semantics(schema)

    assert any(issue.path == "/foreign_keys" for issue in issues)



def test_semantic_validation_rejects_invalid_boolean_and_category_declarations() -> None:
    """Wrongly accepting duplicate lexical declarations changes logical membership."""
    schema = TableSchema(
        fields={
            "enabled": FieldDefinition(
                type=UniversalType.BOOLEAN,
                true_values=["yes", "yes"],
                false_values=["yes"],
            ),
            "status": FieldDefinition(
                type=UniversalType.STRING,
                categories=[
                    LabeledValue("open", "Open"),
                    LabeledValue("open", "Duplicate"),
                ],
            ),
            "amount": FieldDefinition(
                type=UniversalType.INTEGER,
                decimal_char=".",
            ),
        }
    )

    paths = {issue.path for issue in validate_table_schema_semantics(schema)}

    assert {
        "/fields/0/true_values",
        "/fields/0/false_values",
        "/fields/1/categories/1",
        "/fields/2/decimal_char",
    } <= paths


def test_semantic_validation_rejects_ambiguous_missing_value_labels() -> None:
    """Duplicate logical missing values or labels make diagnostics ambiguous."""
    schema = TableSchema(
        fields={
            "note": FieldDefinition(
                type=UniversalType.STRING,
                missing_values=[
                    LabeledValue("NA", "Not available"),
                    LabeledValue("NA", "Repeated value"),
                ],
            )
        },
        missing_values=[
            LabeledValue("NULL", "Missing"),
            LabeledValue("N/A", "Missing"),
        ],
    )

    paths = {issue.path for issue in validate_table_schema_semantics(schema)}

    assert {"/fields/0/missing_values/1", "/missing_values/1"} <= paths


def test_semantic_validation_denies_remote_json_schema_references() -> None:
    """A declaration must never make validation depend on remote schema content."""
    from mountainash.exceptions import JSONSchemaReferenceDenied

    schema = TableSchema(
        fields={
            "payload": FieldDefinition(
                type=UniversalType.OBJECT,
                constraints=FieldConstraints(
                    json_schema={"$ref": "https://example.test/schema.json"}
                ),
            )
        }
    )

    issues = validate_table_schema_semantics(schema)

    assert isinstance(issues[0].cause, JSONSchemaReferenceDenied)


def test_semantic_validation_denies_remote_dynamic_json_schema_references() -> None:
    """Every JSON Schema reference keyword must obey the local-only policy."""
    from mountainash.exceptions import JSONSchemaReferenceDenied

    schema = TableSchema(
        fields={
            "payload": FieldDefinition(
                type=UniversalType.OBJECT,
                constraints=FieldConstraints(
                    json_schema={"$dynamicRef": "https://example.test/schema.json"}
                ),
            )
        }
    )

    issues = validate_table_schema_semantics(schema)

    assert isinstance(issues[0].cause, JSONSchemaReferenceDenied)
