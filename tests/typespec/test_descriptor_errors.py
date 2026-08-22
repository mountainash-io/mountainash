from mountainash import MountainashError
from mountainash.exceptions import (
    DescriptorError,
    DescriptorReferenceInvalid,
    DescriptorReferenceNotFound,
    DescriptorReferenceSchemeDenied,
    InvalidDescriptorRelationship,
    InvalidDescriptorStructure,
    InvalidDescriptorSyntax,
    MissingDescriptorBase,
    UnsupportedDescriptorVersion,
    UnsupportedResourceDialect,
)


def test_descriptor_errors_are_public_and_typed() -> None:
    assert issubclass(DescriptorError, MountainashError)
    assert issubclass(InvalidDescriptorSyntax, ValueError)
    assert issubclass(InvalidDescriptorStructure, ValueError)
    assert issubclass(UnsupportedDescriptorVersion, ValueError)
    assert issubclass(MissingDescriptorBase, ValueError)
    assert issubclass(DescriptorReferenceNotFound, FileNotFoundError)
    assert issubclass(DescriptorReferenceInvalid, ValueError)
    assert issubclass(DescriptorReferenceSchemeDenied, PermissionError)
    assert issubclass(InvalidDescriptorRelationship, ValueError)
    assert issubclass(UnsupportedResourceDialect, ValueError)


def test_descriptor_error_exposes_stable_context() -> None:
    error = DescriptorReferenceInvalid(
        "resolved schema is invalid",
        descriptor_kind="resource",
        descriptor_path="$.resources[0].schema",
        resource_name="orders",
        reference="schema.json",
        normalized_reference="file:///tmp/schema.json",
        expected_kind="schema",
        rejected_value={"resources": []},
        required_form="a Table Schema mapping",
    )
    assert error.descriptor_kind == "resource"
    assert error.descriptor_path == "$.resources[0].schema"
    assert error.resource_name == "orders"
    assert error.reference == "schema.json"
    assert error.normalized_reference == "file:///tmp/schema.json"
    assert error.expected_kind == "schema"
    assert error.rejected_value == {"resources": []}
    assert error.required_form == "a Table Schema mapping"
