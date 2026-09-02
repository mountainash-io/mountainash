import json
from dataclasses import FrozenInstanceError

import pytest

from mountainash.typespec.datapackage import TableDialect
from mountainash.typespec.frictionless import typespec_to_frictionless
from mountainash.typespec.errors import (
    InvalidDescriptorStructure,
    InvalidDescriptorSyntax,
    UnsupportedDescriptorVersion,
)
from mountainash.typespec.frictionless_invariants import (
    InvariantLocation,
    is_recognized_v1_profile,
    parse_descriptor_json,
    pydantic_structure_error,
    reject_v1_markers_at,
    require_package_mapping,
    validate_resource_source_shape,
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


@pytest.mark.parametrize(
    ("raw", "suffix", "required_form"),
    [
        ({"path": "a.csv"}, ".name", "non-empty string resource name"),
        ({"name": "r"}, "", "exactly one of path or data"),
        ({"name": "r", "path": "a.csv", "data": []}, "", "exactly one of path or data"),
        ({"name": "r", "path": []}, ".path", "non-empty string or non-empty list of strings"),
        ({"name": "r", "path": ["a.csv", 1]}, ".path", "string or non-empty list of strings"),
        ({"name": "r", "path": ""}, ".path", "non-empty path string"),
        ({"name": "r", "path": "/tmp/a.csv"}, ".path", "relative local path"),
        ({"name": "r", "path": "../a.csv"}, ".path", "local path without hidden, ., or .. segments"),
        ({"name": "r", "path": "a.csv", "type": "file"}, ".type", "absent or 'table'"),
    ],
)
def test_resource_source_shape_has_exact_public_form(raw, suffix, required_form):
    location = InvariantLocation("$.resources[3]", raw.get("name"), None)
    with pytest.raises(InvalidDescriptorStructure) as caught:
        validate_resource_source_shape(raw, location=location)
    assert caught.value.descriptor_path == f"$.resources[3]{suffix}"
    assert caught.value.required_form == required_form


@pytest.mark.parametrize("text", ["{", "", "not-json"])
def test_parse_descriptor_json_has_one_syntax_error(text):
    with pytest.raises(InvalidDescriptorSyntax) as caught:
        parse_descriptor_json(text)
    assert caught.value.descriptor_path == "$"
    assert caught.value.rejected_value == text
    assert caught.value.required_form == "valid JSON text"


def test_parse_descriptor_json_accepts_json_values():
    assert parse_descriptor_json('{"resources": []}') == {"resources": []}


@pytest.mark.parametrize("raw", [[], None, "package"])
def test_require_package_mapping_rejects_non_mapping_roots(raw):
    with pytest.raises(InvalidDescriptorStructure) as caught:
        require_package_mapping(raw)
    assert caught.value.descriptor_path == "$"
    assert caught.value.rejected_value is raw
    assert caught.value.required_form == "package descriptor mapping"


def test_require_package_mapping_returns_original_mapping():
    raw = {"resources": []}
    assert require_package_mapping(raw) is raw


def test_pydantic_structure_error_uses_recognized_property_form():
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

    class StrictResource(BaseModel):
        model_config = ConfigDict(extra="forbid")
        bytes_: int = Field(alias="bytes")

    with pytest.raises(ValidationError) as caught:
        StrictResource.model_validate({"bytes": []})
    error = pydantic_structure_error(
        caught.value,
        descriptor_kind="resource",
        base_path="$.resources[3]",
        resource_name="r",
        reference=None,
        aliases={"bytes_": "bytes"},
        required_forms={"bytes": "integer"},
    )
    assert error.descriptor_path == "$.resources[3].bytes"
    assert error.rejected_value == []
    assert error.required_form == "integer"

def test_pydantic_structure_error_uses_generic_form_for_forbidden_keyword():
    from pydantic import BaseModel, ConfigDict, ValidationError

    class StrictResource(BaseModel):
        model_config = ConfigDict(extra="forbid")
        name: str

    with pytest.raises(ValidationError) as caught:
        StrictResource.model_validate({"name": "r", "future": True})
    error = pydantic_structure_error(
        caught.value,
        descriptor_kind="resource",
        base_path="$",
        resource_name="r",
        reference=None,
        aliases={"name": "name"},
        required_forms={"name": "non-empty string resource name"},
    )
    assert error.descriptor_path == "$.future"
    assert error.rejected_value is True
    assert error.required_form == "valid resource property value"
