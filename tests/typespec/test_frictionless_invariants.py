import json
from dataclasses import FrozenInstanceError

import pytest

from mountainash.typespec.datapackage import TableDialect
from mountainash.typespec.errors import InvalidDescriptorStructure, UnsupportedDescriptorVersion
from mountainash.typespec.frictionless import typespec_to_frictionless
from mountainash.typespec.frictionless_invariants import (
    InvariantLocation,
    is_recognized_v1_profile,
    reject_v1_markers_at,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def test_profile_identity_uses_normalized_host_and_exact_path() -> None:
    assert is_recognized_v1_profile(
        "HTTPS://WWW.SPECS.FRICTIONLESSDATA.IO/schemas/csv-dialect.json?x=1#y"
    )
    assert not is_recognized_v1_profile(
        "https://specs.frictionlessdata.io/schemas/CSV-dialect.json"
    )


def test_profile_identity_ignores_userinfo_and_port() -> None:
    assert is_recognized_v1_profile(
        "https://user:pass@WWW.FRICTIONLESSDATA.IO:8443/schemas/table-schema.json"
    )


def test_non_string_profile_has_exact_structure_error() -> None:
    location = InvariantLocation("$.resources[2].dialect", "orders", None)
    with pytest.raises(InvalidDescriptorStructure) as caught:
        reject_v1_markers_at(
            {"$schema": 1}, descriptor_kind="dialect", location=location
        )
    assert caught.value.descriptor_path == "$.resources[2].dialect.$schema"
    assert caught.value.rejected_value == 1
    assert caught.value.required_form == "profile URI string"


def test_v1_presence_marker_wins_before_property_validation() -> None:
    location = InvariantLocation("$.resources[0].dialect", "orders", None)
    with pytest.raises(UnsupportedDescriptorVersion) as caught:
        reject_v1_markers_at(
            {"caseSensitiveHeader": None}, descriptor_kind="dialect", location=location
        )
    assert caught.value.descriptor_path.endswith(".caseSensitiveHeader")
    assert caught.value.required_form == "v2 dialect properties"


def test_location_is_immutable_and_reference_root_can_be_rebased() -> None:
    location = InvariantLocation("$.schema", "orders")
    assert location.child("$schema").descriptor_path == "$.schema.$schema"
    assert location.with_reference("schema.json").descriptor_path == "$"
    assert location.with_reference("schema.json").reference == "schema.json"
    with pytest.raises(FrozenInstanceError):
        location.descriptor_path = "$"  # type: ignore[misc]


@pytest.mark.parametrize("schema_url", ["https://example.com/custom", None])
def test_typed_profile_boundaries_allow_unknown_or_absent(schema_url: str | None) -> None:
    dialect = TableDialect(schema_url=schema_url)
    assert dialect.schema_url == schema_url
    spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)], schema_url=schema_url)
    assert typespec_to_frictionless(spec).get("$schema") == schema_url


def test_typed_profile_fields_reject_v1_and_are_immutable() -> None:
    with pytest.raises(UnsupportedDescriptorVersion):
        TableDialect(schema_url="https://datapackage.org/profiles/1.0/tabledialect.json")
    with pytest.raises(UnsupportedDescriptorVersion):
        TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
            schema_url="https://datapackage.org/profiles/1.0/tableschema.json",
        )
    dialect = TableDialect(schema_url="https://example.com/custom")
    with pytest.raises(TypeError):
        dialect.schema_url = "https://example.com/other"
    spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
    with pytest.raises(TypeError):
        spec.schema_url = "https://example.com/other"


def test_typed_dialect_extras_apply_presence_marker_policy() -> None:
    with pytest.raises(UnsupportedDescriptorVersion):
        TableDialect(extras={"caseSensitiveHeader": False})
    dialect = TableDialect(extras={"future": True})
    assert dialect.to_descriptor() == {"future": True}


def test_typed_validation_entrypoints_keep_leaf_exceptions() -> None:
    uri = "https://datapackage.org/profiles/1.0/tabledialect.json"
    for build in (
        lambda: TableDialect.model_validate({"schema_url": uri}),
        lambda: TableDialect.model_validate_json(json.dumps({"schema_url": uri})),
    ):
        with pytest.raises(UnsupportedDescriptorVersion):
            build()


def test_serializers_revalidate_mutated_typed_profile_fields() -> None:
    dialect = TableDialect(schema_url="https://example.com/custom")
    object.__setattr__(dialect, "schema_url", "https://datapackage.org/profiles/1.0/tabledialect.json")
    with pytest.raises(UnsupportedDescriptorVersion):
        dialect.to_descriptor()

    spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
    object.__setattr__(spec, "schema_url", "https://datapackage.org/profiles/1.0/tableschema.json")
    with pytest.raises(UnsupportedDescriptorVersion):
        typespec_to_frictionless(spec)
