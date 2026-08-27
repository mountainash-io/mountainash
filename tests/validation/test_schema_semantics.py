"""TypeSpec semantic declaration validation."""

import pytest

from mountainash.exceptions import (
    AmbiguousFieldName,
    InvalidConstraintDeclaration,
    InvalidFieldIdentifier,
    InvalidTypeSpecSemantics,
    TypeSpecError,
)
from mountainash.typespec import (
    FieldConstraints,
    LabeledValue,
    FieldSpec,
    ForeignKey,
    ForeignKeyReference,
    TypeSpec,
    UniversalType,
)
from mountainash.validation import require_valid_typespec, validate_typespec_semantics


def test_semantic_issues_are_complete_and_deterministically_ordered() -> None:
    """Removing deterministic aggregation would hide independent declaration faults."""
    spec = TypeSpec(
        fields=[
            FieldSpec(name="", type=UniversalType.STRING),
            FieldSpec(
                name="amount",
                type=UniversalType.INTEGER,
                constraints=FieldConstraints(min_length=-1, pattern="["),
            ),
        ]
    )

    issues = validate_typespec_semantics(spec)

    assert tuple((issue.path, issue.code) for issue in issues) == tuple(
        sorted((issue.path, issue.code) for issue in issues)
    )
    assert {type(issue.cause) for issue in issues} >= {
        InvalidFieldIdentifier,
        InvalidConstraintDeclaration,
    }


def test_require_valid_typespec_raises_one_aggregate() -> None:
    """Removing the execution boundary must prevent invalid declarations running."""
    spec = TypeSpec(fields=[FieldSpec(name="", type=UniversalType.STRING)])

    with pytest.raises(InvalidTypeSpecSemantics) as caught:
        require_valid_typespec(spec, resource_name="orders")

    assert caught.value.resource_name == "orders"
    assert caught.value.issues == validate_typespec_semantics(
        spec, resource_name="orders"
    )
    assert isinstance(caught.value, TypeSpecError)


def test_duplicate_names_are_rejected_at_the_operational_boundary() -> None:
    """Accepting duplicate names would make name-addressed checks ambiguous."""
    spec = TypeSpec(
        fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="id", type=UniversalType.STRING),
        ]
    )

    issue = validate_typespec_semantics(spec)[0]

    assert issue.path == "/fields/1/name"
    assert isinstance(issue.cause, AmbiguousFieldName)


@pytest.mark.parametrize(
    ("mutate", "path"),
    [
        (lambda field: setattr(field, "format", "fmt:%Y"), "/fields/0/format"),
        (lambda field: setattr(field, "item_type", "object"), "/fields/0/item_type"),
        (
            lambda field: setattr(field.constraints, "required", 1),
            "/fields/0/constraints/required",
        ),
    ],
)
def test_semantic_validation_rechecks_mutated_programmatic_properties(
    mutate, path: str
) -> None:
    """Bypassing dataclass construction must not bypass declaration validation."""
    field = FieldSpec(
        name="values",
        type=UniversalType.LIST,
        constraints=FieldConstraints(required=True),
    )
    mutate(field)

    issues = validate_typespec_semantics(TypeSpec(fields=[field]))

    assert any(issue.path == path for issue in issues)


def test_semantic_validation_checks_package_foreign_key_target_fields() -> None:
    """A typo in a package key target must fail before any resource is read."""
    orders = TypeSpec(
        fields=[FieldSpec(name="customer_id", type=UniversalType.INTEGER)],
        foreign_keys=[
            ForeignKey(
                fields=["customer_id"],
                reference=ForeignKeyReference(resource="customers", fields=["missing"]),
            )
        ],
    )
    customers = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])

    issues = validate_typespec_semantics(
        orders,
        resource_name="orders",
        package_resource_names=frozenset({"orders", "customers"}),
        package_specs={"orders": orders, "customers": customers},
    )
    assert any(issue.path == "/foreign_keys/0/reference/fields/0" for issue in issues)


def test_semantic_validation_rejects_an_explicitly_empty_foreign_key_list() -> None:
    """Treating [] like omission loses an invalid explicit declaration."""
    spec = TypeSpec(
        fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
        foreign_keys=[],
    )

    issues = validate_typespec_semantics(spec)

    assert any(issue.path == "/foreign_keys" for issue in issues)



def test_semantic_validation_rejects_invalid_boolean_and_category_declarations() -> None:
    """Wrongly accepting duplicate lexical declarations changes logical membership."""
    spec = TypeSpec(
        fields=[
            FieldSpec(
                name="enabled",
                type=UniversalType.BOOLEAN,
                true_values=["yes", "yes"],
                false_values=["yes"],
            ),
            FieldSpec(
                name="status",
                type=UniversalType.STRING,
                categories=[
                    LabeledValue("open", "Open"),
                    LabeledValue("open", "Duplicate"),
                ],
            ),
            FieldSpec(
                name="amount",
                type=UniversalType.INTEGER,
                decimal_char=".",
            ),
        ]
    )

    paths = {issue.path for issue in validate_typespec_semantics(spec)}

    assert {
        "/fields/0/true_values",
        "/fields/0/false_values",
        "/fields/1/categories/1",
        "/fields/2/decimal_char",
    } <= paths


def test_semantic_validation_rejects_ambiguous_missing_value_labels() -> None:
    """Duplicate logical missing values or labels make diagnostics ambiguous."""
    spec = TypeSpec(
        fields=[
            FieldSpec(
                name="note",
                type=UniversalType.STRING,
                missing_values=[
                    LabeledValue("NA", "Not available"),
                    LabeledValue("NA", "Repeated value"),
                ],
            )
        ],
        missing_values=[
            LabeledValue("NULL", "Missing"),
            LabeledValue("N/A", "Missing"),
        ],
    )

    paths = {issue.path for issue in validate_typespec_semantics(spec)}

    assert {"/fields/0/missing_values/1", "/missing_values/1"} <= paths


def test_semantic_validation_denies_remote_json_schema_references() -> None:
    """A declaration must never make validation depend on remote schema content."""
    from mountainash.exceptions import JSONSchemaReferenceDenied

    spec = TypeSpec(
        fields=[
            FieldSpec(
                name="payload",
                type=UniversalType.OBJECT,
                constraints=FieldConstraints(
                    json_schema={"$ref": "https://example.test/schema.json"}
                ),
            )
        ]
    )

    issues = validate_typespec_semantics(spec)

    assert isinstance(issues[0].cause, JSONSchemaReferenceDenied)


def test_semantic_validation_denies_remote_dynamic_json_schema_references() -> None:
    """Every JSON Schema reference keyword must obey the local-only policy."""
    from mountainash.exceptions import JSONSchemaReferenceDenied

    spec = TypeSpec(
        fields=[
            FieldSpec(
                name="payload",
                type=UniversalType.OBJECT,
                constraints=FieldConstraints(
                    json_schema={"$dynamicRef": "https://example.test/schema.json"}
                ),
            )
        ]
    )

    issues = validate_typespec_semantics(spec)

    assert isinstance(issues[0].cause, JSONSchemaReferenceDenied)
