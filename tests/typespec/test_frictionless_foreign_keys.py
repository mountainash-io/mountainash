"""Round-trip tests for the reusable ForeignKey dict<->object helpers."""
from __future__ import annotations

from types import MappingProxyType
from typing import Any

import pytest

from mountainash.exceptions import InvalidDescriptorRelationship
from mountainash.typespec.datapackage import DataPackage, TableDialect
from mountainash.typespec.descriptor_context import DescriptorKind
from mountainash.typespec.frictionless import (
    foreign_key_from_dict,
    foreign_key_to_dict,
    typespec_from_frictionless,
)
from mountainash.typespec.frictionless_invariants import (
    InvariantLocation,
    validate_foreign_key_targets,
)
from mountainash.typespec.spec import ForeignKey, ForeignKeyReference


RAW = {
    "fields": ["customer_id"],
    "reference": {"resource": "customers", "fields": ["id"]},
}


def test_foreign_key_from_dict():
    fk = foreign_key_from_dict(RAW)
    assert fk.fields == ["customer_id"]
    assert fk.reference.resource == "customers"
    assert fk.reference.fields == ["id"]


def test_foreign_key_to_dict():
    fk = ForeignKey(
        fields=["customer_id"],
        reference=ForeignKeyReference(resource="customers", fields=["id"]),
    )
    assert foreign_key_to_dict(fk) == RAW


def test_round_trip_is_identity():
    assert foreign_key_to_dict(foreign_key_from_dict(RAW)) == RAW


def test_self_reference_empty_resource_normalizes_to_none():
    raw = {"fields": ["parent_id"], "reference": {"resource": "", "fields": ["id"]}}
    fk = foreign_key_from_dict(raw)
    # "" is the raw self-reference marker; the typed model normalizes it to None
    assert fk.reference.resource is None
    # the writer omits the resource key entirely for a self-reference
    assert foreign_key_to_dict(fk) == {"fields": ["parent_id"], "reference": {"fields": ["id"]}}


def test_self_reference_absent_resource_is_none():
    raw = {"fields": ["parent_id"], "reference": {"fields": ["id"]}}
    fk = foreign_key_from_dict(raw)
    assert fk.reference.resource is None
    assert foreign_key_to_dict(fk) == raw


def test_adapters_accept_mapping_without_mutating_input() -> None:
    schema = {
        "fields": [{"name": "id", "type": "integer"}],
        "foreignKeys": [RAW],
    }
    schema_view = MappingProxyType(schema)
    expected = dict(schema)

    spec = typespec_from_frictionless(schema_view)
    dialect_input = MappingProxyType({"delimiter": ";"})
    dialect = TableDialect.from_descriptor(dialect_input)

    assert spec.field_names == ["id"]
    assert dialect.delimiter == ";"
    assert schema == expected
    assert dict(dialect_input) == {"delimiter": ";"}


def test_inline_foreign_key_target_is_validated_during_package_construction() -> None:
    with pytest.raises(InvalidDescriptorRelationship):
        DataPackage.from_descriptor(
            {
                "resources": [
                    {
                        "name": "orders",
                        "path": "orders.csv",
                        "schema": {
                            "fields": [{"name": "customer_id"}],
                            "foreignKeys": [RAW],
                        },
                    }
                ]
            }
        )


class _RecordingResolver:
    def __init__(self, document: dict[str, Any]) -> None:
        self.document = document
        self.calls: list[tuple[str, DescriptorKind]] = []

    def resolve(self, reference, *, base_uri, expected_kind):
        self.calls.append((reference, expected_kind))
        return dict(self.document)


def test_resolved_foreign_key_target_is_validated_by_typed_accessor() -> None:
    resolver = _RecordingResolver(
        {
            "fields": [{"name": "customer_id"}],
            "foreignKeys": [RAW],
        }
    )
    package = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": "schema.json",
                }
            ]
        },
        base_uri="file:///tmp/descriptors/",
        resolver=resolver,
    )

    assert resolver.calls == []
    with pytest.raises(InvalidDescriptorRelationship):
        package.resources[0].to_typespec()
    assert resolver.calls == [("schema.json", DescriptorKind.SCHEMA)]


def test_authored_none_reference_is_the_canonical_self_reference() -> None:
    reference = ForeignKeyReference(None, ["id"])
    assert reference.resource is None


def test_authored_empty_reference_resource_is_invalid_relationship() -> None:
    with pytest.raises(InvalidDescriptorRelationship) as caught:
        ForeignKeyReference("", ["id"])
    assert caught.value.descriptor_path == "foreign_key.reference.resource"
    assert caught.value.required_form == "None or non-empty resource name string"


def test_authored_non_string_reference_resource_is_invalid_relationship() -> None:
    with pytest.raises(InvalidDescriptorRelationship) as caught:
        ForeignKeyReference(1, ["id"])  # type: ignore[arg-type]
    assert caught.value.rejected_value == 1
    assert caught.value.required_form == "None or non-empty resource name string"


def test_foreign_key_target_validation_rejects_unknown_package_resource() -> None:
    foreign_keys = (foreign_key_from_dict(RAW),)
    location = InvariantLocation("$.resources[1].schema", "orders", None)
    with pytest.raises(InvalidDescriptorRelationship) as caught:
        validate_foreign_key_targets(
            foreign_keys,
            child_name="orders",
            resource_names=frozenset({"orders"}),
            location=location,
        )
    assert caught.value.descriptor_path == (
        "$.resources[1].schema.foreignKeys[0].reference.resource"
    )
    assert caught.value.rejected_value == "customers"


def test_foreign_key_target_validation_allows_explicit_package_self_reference() -> None:
    foreign_keys = (
        ForeignKey(
            fields=["parent_id"],
            reference=ForeignKeyReference("orders", ["id"]),
        ),
    )
    validate_foreign_key_targets(
        foreign_keys,
        child_name="orders",
        resource_names=frozenset({"orders"}),
        location=InvariantLocation("$.schema", "orders", None),
    )
