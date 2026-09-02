from copy import deepcopy
import json

import mountainash as ma
import pytest

from mountainash import DescriptorWriteMode
from mountainash.exceptions import (
    InvalidDescriptorStructure,
    InvalidDescriptorSyntax,
    InvalidDescriptorRelationship,
    UnsupportedDescriptorVersion,
    UnsupportedResourceDialect,
)
from mountainash.typespec.datapackage import DataPackage, DataResource, TableDialect
from mountainash.typespec.frictionless import typespec_to_frictionless
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


def minimal_descriptor() -> dict[str, object]:
    return {"resources": [{"name": "orders", "path": "orders.csv"}]}


def test_from_descriptor_accepts_only_a_mapping() -> None:
    with pytest.raises(InvalidDescriptorStructure):
        DataPackage.from_descriptor("datapackage.json")  # type: ignore[arg-type]


def test_from_json_decodes_json_text() -> None:
    package = DataPackage.from_json(json.dumps(minimal_descriptor()))
    assert package.resources[0].name == "orders"


def test_from_path_sets_parent_directory_base(tmp_path) -> None:
    path = tmp_path / "datapackage.json"
    path.write_text(json.dumps(minimal_descriptor()), encoding="utf-8")
    package = DataPackage.from_path(path)
    assert package._descriptor_context.base_uri == tmp_path.resolve().as_uri() + "/"


def test_from_path_keeps_utf8_error_distinct(tmp_path) -> None:
    path = tmp_path / "datapackage.json"
    path.write_bytes(b"\xff")
    with pytest.raises(InvalidDescriptorSyntax) as caught:
        DataPackage.from_path(path)
    assert caught.value.descriptor_path == "$"
    assert caught.value.rejected_value == path
    assert caught.value.required_form == "UTF-8 JSON text"


def test_decode_does_not_mutate_input() -> None:
    raw = minimal_descriptor()
    expected = deepcopy(raw)
    DataPackage.from_descriptor(raw)
    assert raw == expected


def test_decoder_owns_descriptor_metadata() -> None:
    payload = [{"id": 1}]
    schema = {"fields": [{"name": "id"}]}
    dialect = {"delimiter": ";"}
    raw = {
        "resources": [
            {
                "name": "orders",
                "data": payload,
                "schema": schema,
                "dialect": dialect,
            }
        ]
    }
    resource = DataPackage.from_descriptor(raw).resources[0]
    assert resource.data == payload
    assert resource.table_schema == schema
    assert resource.table_schema is not schema
    assert resource.dialect == dialect
    assert resource.dialect is not dialect

@pytest.mark.parametrize(
    "contributors",
    [
        [{"title": "A", "roles": ["author"]}],
        [{"title": "A", "role": "author"}],
        [{"title": "A", "role": "ignored", "roles": ["owner"]}],
    ],
)
def test_contributor_consumer_forms_are_stored(contributors) -> None:
    raw = minimal_descriptor() | {"contributors": contributors}
    package = DataPackage.from_descriptor(raw)
    assert package.contributors == contributors


def test_absent_schema_is_v2() -> None:
    assert DataPackage.from_descriptor(minimal_descriptor()).dollar_schema is None


def test_standard_v2_schema_is_accepted() -> None:
    raw = minimal_descriptor() | {
        "$schema": "https://datapackage.org/profiles/2.0/datapackage.json"
    }
    assert DataPackage.from_descriptor(raw).dollar_schema == raw["$schema"]


def test_unknown_non_v1_schema_is_preserved() -> None:
    raw = minimal_descriptor() | {"$schema": "https://example.com/profiles/custom.json"}
    package = DataPackage.from_descriptor(raw)
    assert package.dollar_schema == raw["$schema"]


@pytest.mark.parametrize("path", ["orders.csv", ["orders-1.csv", "orders-2.csv"]])
def test_path_consumer_forms_are_accepted(path) -> None:
    package = DataPackage.from_descriptor({"resources": [{"name": "orders", "path": path}]})
    assert package.resources[0].path == path


def test_data_without_path_is_accepted() -> None:
    raw = {"resources": [{"name": "orders", "data": [{"id": 1}]}]}
    assert DataPackage.from_descriptor(raw).resources[0].data == [{"id": 1}]


@pytest.mark.parametrize("resource_type", [None, "table"])
def test_resource_type_forms_are_accepted(resource_type) -> None:
    resource = {"name": "orders", "path": "orders.csv"}
    if resource_type is not None:
        resource["type"] = resource_type
    assert DataPackage.from_descriptor({"resources": [resource]}).resources[0].type == resource_type


def test_dots_inside_normal_file_name_are_accepted() -> None:
    package = DataPackage.from_descriptor(
        {"resources": [{"name": "orders", "path": "orders.v2.csv"}]}
    )
    assert package.resources[0].path == "orders.v2.csv"


def test_remote_resource_url_skips_local_hidden_path_check() -> None:
    raw = {"resources": [{"name": "orders", "path": "https://example.com/.hidden.csv"}]}
    assert DataPackage.from_descriptor(raw).resources[0].path == raw["resources"][0]["path"]


@pytest.mark.parametrize(
    "resource_fields",
    [
        {"bytes": 12},
        {"hash": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
        {"created": "2024-01-02T03:04:05Z"},
    ],
)
def test_valid_resource_metadata_is_accepted(resource_fields) -> None:
    raw = {"resources": [{"name": "orders", "path": "orders.csv", **resource_fields}]}
    package = DataPackage.from_descriptor(raw)
    assert package.resources[0].bytes_ == resource_fields.get("bytes")


def test_valid_package_created_is_preserved() -> None:
    raw = {**minimal_descriptor(), "created": "2024-01-02T03:04:05Z"}
    package = DataPackage.from_descriptor(raw)
    assert package.created == raw["created"]


def test_inline_schema_and_dialect_mappings_stay_raw() -> None:
    schema = {"fields": [{"name": "id", "type": "integer"}]}
    dialect = {"delimiter": ";"}
    raw = {"resources": [{"name": "orders", "path": "orders.csv", "schema": schema, "dialect": dialect}]}
    resource = DataPackage.from_descriptor(raw).resources[0]
    assert resource.table_schema == schema
    assert resource.dialect == dialect


def test_schema_and_dialect_reference_strings_stay_raw() -> None:
    raw = {
        "resources": [
            {"name": "orders", "path": "orders.csv", "schema": "schema.json", "dialect": "dialect.json"}
        ]
    }
    resource = DataPackage.from_descriptor(raw).resources[0]
    assert resource.table_schema == "schema.json"
    assert resource.dialect == "dialect.json"


def test_unknown_extension_properties_are_preserved_at_each_level() -> None:
    raw = {
        "packageExtension": {"enabled": True},
        "resources": [
            {
                "name": "orders",
                "path": "orders.csv",
                "resourceExtension": "r",
                "schema": {"fields": [], "schemaExtension": 1},
                "dialect": {"delimiter": ";", "dialectExtension": 2},
            }
        ],
    }
    package = DataPackage.from_descriptor(raw)
    resource = package.resources[0]
    assert package.extras["packageExtension"] == {"enabled": True}
    assert resource.extras["resourceExtension"] == "r"
    assert resource.table_schema["schemaExtension"] == 1
    assert resource.dialect["dialectExtension"] == 2

@pytest.mark.parametrize(
    "profile_uri",
    [
        "https://datapackage.org/schemas/data-package.json",
        "https://specs.frictionlessdata.io/profiles/1.0/datapackage.json",
    ],
)
def test_unrecognized_cross_family_profile_uris_are_preserved(profile_uri) -> None:
    raw = {"$schema": profile_uri, **minimal_descriptor()}
    assert DataPackage.from_descriptor(raw).dollar_schema == profile_uri


def test_mixed_local_and_remote_path_array_is_accepted() -> None:
    path = ["orders.csv", "https://example.com/orders-2.csv"]
    package = DataPackage.from_descriptor({"resources": [{"name": "orders", "path": path}]})
    assert package.resources[0].path == path


def test_negative_integer_bytes_is_accepted() -> None:
    raw = {"resources": [{"name": "orders", "path": "orders.csv", "bytes": -1}]}
    assert DataPackage.from_descriptor(raw).resources[0].bytes_ == -1

def test_decoder_binds_one_shared_context_and_inherited_sources() -> None:
    raw = {
        "sources": [{"title": "catalog", "extension": {"owner": "team"}}],
        "resources": [
            {"name": "orders", "path": "orders.csv"},
            {"name": "customers", "path": "customers.csv", "sources": [{"title": "local"}]},
        ],
    }
    package = DataPackage.from_descriptor(raw)
    first, second = package.resources
    assert package._descriptor_context is first._descriptor_context
    assert first._descriptor_context is second._descriptor_context
    assert first._package_resource_names is second._package_resource_names
    assert first._package_resource_names == frozenset({"orders", "customers"})
    assert first.effective_sources == raw["sources"]
    assert second.effective_sources == raw["resources"][1]["sources"]


_V1_URIS = [
    *(f"{scheme}://datapackage.org/profiles/1.0/{name}.json" for scheme in ("http", "https") for name in ("datapackage", "dataresource", "tabledialect", "tableschema")),
    *(f"{scheme}://{www}specs.frictionlessdata.io/schemas/{name}.json" for scheme in ("http", "https") for www in ("", "www.") for name in ("data-package", "data-resource", "tabular-data-resource", "tabular-data-package", "fiscal-data-package", "table-schema", "csv-dialect")),
    *(f"{scheme}://{www}frictionlessdata.io/schemas/{name}.json" for scheme in ("http", "https") for www in ("", "www.") for name in ("data-package", "data-resource", "tabular-data-resource", "tabular-data-package", "fiscal-data-package", "table-schema", "csv-dialect")),
]


@pytest.mark.parametrize("profile_uri", _V1_URIS)
def test_every_recognized_v1_profile_uri_is_rejected(profile_uri) -> None:
    with pytest.raises(UnsupportedDescriptorVersion) as caught:
        DataPackage.from_descriptor({"$schema": profile_uri, **minimal_descriptor()})
    assert caught.value.descriptor_path == "$.$schema"
    assert caught.value.rejected_value == profile_uri
    assert caught.value.required_form


@pytest.mark.parametrize("profile_uri", [_V1_URIS[0] + "?x=1", _V1_URIS[0] + "#frag"])
def test_v1_profile_query_and_fragment_are_rejected(profile_uri) -> None:
    with pytest.raises(UnsupportedDescriptorVersion):
        DataPackage.from_descriptor({"$schema": profile_uri, **minimal_descriptor()})


def test_profile_markers_are_rejected() -> None:
    for raw, expected_path, expected_value in (
        (
            {"profile": "https://example.com/v1", **minimal_descriptor()},
            "$.profile",
            "https://example.com/v1",
        ),
        (
            {"resources": [{"name": "orders", "path": "orders.csv", "profile": "v1"}]},
            "$.resources[0].profile",
            "v1",
        ),
    ):
        with pytest.raises(UnsupportedDescriptorVersion) as caught:
            DataPackage.from_descriptor(raw)
        assert caught.value.descriptor_path == expected_path
        assert caught.value.rejected_value == expected_value
        assert caught.value.required_form



@pytest.mark.parametrize(
    "raw",
    [
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "$schema": _V1_URIS[0],
                }
            ]
        },
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": {"$schema": _V1_URIS[0], "fields": []},
                }
            ]
        },
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "dialect": {"$schema": _V1_URIS[0]},
                }
            ]
        },
    ],
)
def test_v1_schema_markers_are_rejected_at_nested_levels(raw) -> None:
    with pytest.raises(UnsupportedDescriptorVersion) as caught:
        DataPackage.from_descriptor(raw)
    assert caught.value.rejected_value == _V1_URIS[0]
    assert caught.value.required_form


def test_v1_dialect_markers_are_rejected() -> None:
    for marker in ("caseSensitiveHeader", "csvddfVersion"):
        raw = {"resources": [{"name": "orders", "path": "orders.csv", "dialect": {marker: True}}]}
        with pytest.raises(UnsupportedDescriptorVersion) as caught:
            DataPackage.from_descriptor(raw)
        assert caught.value.descriptor_path == f"$.resources[0].dialect.{marker}"
        assert caught.value.rejected_value is True
        assert caught.value.required_form


@pytest.mark.parametrize(
    "raw",
    [
        {"contributors": [{}], **minimal_descriptor()},
        {"contributors": [{"title": 42}], **minimal_descriptor()},
        {"licenses": [{"name": 42}], **minimal_descriptor()},
        {"sources": [{"title": 42}], **minimal_descriptor()},
    ],
)
def test_malformed_metadata_is_rejected(raw) -> None:
    with pytest.raises(InvalidDescriptorStructure):
        DataPackage.from_descriptor(raw)


def test_invalid_created_is_rejected() -> None:
    with pytest.raises(InvalidDescriptorStructure) as caught:
        DataPackage.from_descriptor({"created": "not-a-date", **minimal_descriptor()})
    assert caught.value.descriptor_path == "$.created"


def test_duplicate_resource_names_are_rejected() -> None:
    raw = {"resources": [{"name": "orders", "path": "a.csv"}, {"name": "orders", "path": "b.csv"}]}
    with pytest.raises(InvalidDescriptorStructure):
        DataPackage.from_descriptor(raw)


@pytest.mark.parametrize(
    "resource",
    [
        {"name": "orders"},
        {"name": "orders", "path": "a.csv", "data": []},
        {"name": "orders", "path": []},
        {"name": "orders", "path": ["a.csv", 2]},
    ],
)
def test_invalid_path_data_shapes_are_rejected(resource) -> None:
    with pytest.raises(InvalidDescriptorStructure):
        DataPackage.from_descriptor({"resources": [resource]})


@pytest.mark.parametrize("path", [".hidden/orders.csv", "orders/./data.csv", "orders/../data.csv"])
def test_hidden_and_traversal_local_paths_are_rejected(path) -> None:
    with pytest.raises(InvalidDescriptorStructure):
        DataPackage.from_descriptor({"resources": [{"name": "orders", "path": path}]})


@pytest.mark.parametrize("key,value", [("bytes", True), ("bytes", "12"), ("hash", "bad"), ("hash", 4)])
def test_invalid_bytes_and_hash_shapes_are_rejected(key, value) -> None:
    with pytest.raises(InvalidDescriptorStructure):
        DataPackage.from_descriptor({"resources": [{"name": "orders", "path": "o.csv", key: value}]})


def test_only_table_resource_type_is_supported() -> None:
    with pytest.raises(InvalidDescriptorStructure):
        DataPackage.from_descriptor({"resources": [{"name": "orders", "path": "o.csv", "type": "file"}]})


def test_mixed_dialect_families_are_rejected() -> None:
    raw = {
        "resources": [{"name": "orders", "path": "o.csv", "dialect": {"delimiter": ";", "sheetName": "Sheet1"}}]
    }
    with pytest.raises(UnsupportedResourceDialect):
        DataPackage.from_descriptor(raw)

def test_spreadsheet_dialect_accepts_shared_header_properties() -> None:
    package = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.xlsx",
                    "dialect": {"sheetName": "Orders", "headerRows": [1, 2]},
                }
            ]
        }
    )

    assert package.resources[0].dialect == {"sheetName": "Orders", "headerRows": [1, 2]}


def test_unknown_foreign_key_target_is_rejected() -> None:
    schema = {
        "fields": [{"name": "id", "type": "integer"}],
        "foreignKeys": [{"fields": "id", "reference": {"resource": "missing", "fields": "id"}}],
    }
    with pytest.raises(InvalidDescriptorRelationship):
        DataPackage.from_descriptor({"resources": [{"name": "orders", "path": "o.csv", "schema": schema}]})


def test_top_level_array_is_rejected() -> None:
    with pytest.raises(InvalidDescriptorStructure):
        DataPackage.from_descriptor([])  # type: ignore[arg-type]


def test_malformed_json_is_rejected() -> None:
    with pytest.raises(InvalidDescriptorSyntax) as caught:
        DataPackage.from_json("{")
    assert caught.value.__cause__ is not None



@pytest.mark.parametrize(
    ("decode", "rejected"),
    [
        (lambda: DataPackage.from_json("{"), "{"),
        (lambda: DataPackage.model_validate_json("{"), "{"),
        (lambda: DataPackage.model_validate_json(b"\xff"), b"\xff"),
    ],
)
def test_json_entrypoints_share_syntax_error(decode, rejected) -> None:
    with pytest.raises(InvalidDescriptorSyntax) as caught:
        decode()
    assert caught.value.descriptor_path == "$"
    assert caught.value.rejected_value == rejected
    assert caught.value.required_form == "valid JSON text"


@pytest.mark.parametrize(
    "decode",
    [
        lambda: DataPackage.from_json("[]"),
        lambda: DataPackage.model_validate_json("[]"),
    ],
)
def test_json_entrypoints_share_package_root_error(decode) -> None:
    with pytest.raises(InvalidDescriptorStructure) as caught:
        decode()
    assert caught.value.descriptor_path == "$"
    assert caught.value.rejected_value == []
    assert caught.value.required_form == "package descriptor mapping"


@pytest.mark.parametrize("text", ['{}', '{"resources": []}'])
def test_json_entrypoints_reject_missing_or_empty_resources(text) -> None:
    for decode in (
        lambda: DataPackage.from_json(text),
        lambda: DataPackage.model_validate_json(text),
    ):
        with pytest.raises(InvalidDescriptorStructure) as caught:
            decode()
        assert caught.value.descriptor_path == "$.resources"
        assert caught.value.required_form == "non-empty resource sequence"

def test_resource_decoder_is_removed() -> None:
    from mountainash.typespec.datapackage import DataResource

    assert not hasattr(DataResource, "from_descriptor")

PACKAGE_PROFILE = "https://datapackage.org/profiles/2.0/datapackage.json"
RESOURCE_PROFILE = "https://datapackage.org/profiles/2.0/dataresource.json"
SCHEMA_PROFILE = "https://datapackage.org/profiles/2.0/tableschema.json"
DIALECT_PROFILE = "https://datapackage.org/profiles/2.0/tabledialect.json"


def complete_v2_descriptor() -> dict[str, object]:
    return {
        "$schema": PACKAGE_PROFILE,
        "id": "urn:example:package",
        "name": "example",
        "title": "Example",
        "description": "Descriptor coverage fixture",
        "homepage": "https://example.com",
        "version": "1.0.0",
        "created": "2026-08-20T12:00:00Z",
        "keywords": ["example"],
        "licenses": [{"name": "CC-BY-4.0"}],
        "contributors": [{"title": "Author", "role": "author"}],
        "sources": [{"title": "Catalog", "path": "https://example.com/catalog"}],
        "image": "https://example.com/image.png",
        "futurePackage": {"enabled": True},
        "resources": [
            {
                "$schema": RESOURCE_PROFILE,
                "name": "orders",
                "path": "orders.csv",
                "type": "table",
                "title": "Orders",
                "description": "Order rows",
                "homepage": "https://example.com/orders",
                "format": "csv",
                "mediatype": "text/csv",
                "encoding": "utf-8",
                "bytes": 12,
                "hash": "d25c9c77f588f5dc32059d2da1136c02",
                "licenses": [{"name": "CC-BY-4.0"}],
                "sources": [{"title": "Orders source"}],
                "dialect": {
                    "$schema": DIALECT_PROFILE,
                    "delimiter": ";",
                    "futureDialect": True,
                },
                "schema": {
                    "$schema": SCHEMA_PROFILE,
                    "fields": [{"name": "id", "type": "integer"}],
                    "primaryKey": "id",
                    "foreignKeys": [
                        {
                            "fields": "id",
                            "reference": {"resource": "", "fields": "id"},
                        }
                    ],
                    "futureSchema": True,
                },
                "futureResource": True,
            }
        ],
    }


def expected_canonical_descriptor() -> dict[str, object]:
    expected = deepcopy(complete_v2_descriptor())
    expected["contributors"] = [{"title": "Author", "roles": ["author"]}]
    schema = expected["resources"][0]["schema"]
    schema["primaryKey"] = ["id"]
    schema["foreignKeys"][0]["fields"] = ["id"]
    schema["foreignKeys"][0]["reference"] = {"fields": ["id"]}
    return expected


def test_preserve_and_canonical_outputs_are_independently_owned() -> None:
    package = DataPackage.from_descriptor(complete_v2_descriptor())
    preserve = package.to_descriptor()
    canonical = package.to_canonical_descriptor()
    preserve["resources"][0]["schema"]["fields"][0]["name"] = "changed"
    canonical["contributors"][0]["roles"].append("changed")
    assert package.to_descriptor() == complete_v2_descriptor()
    assert package.to_canonical_descriptor() == expected_canonical_descriptor()


def test_canonical_preserves_extension_profile_identity() -> None:
    raw = complete_v2_descriptor()
    raw["$schema"] = "https://example.com/profiles/custom-package"
    result = DataPackage.from_descriptor(raw).to_canonical_descriptor()
    assert result["$schema"] == raw["$schema"]


@pytest.mark.parametrize(
    ("contributors", "canonical_roles"),
    [
        ([{"title": "A", "roles": ["author"]}], ["author"]),
        ([{"title": "A", "role": "author"}], ["author"]),
        ([{"title": "A", "role": "ignored", "roles": ["owner"]}], ["owner"]),
    ],
)
def test_canonical_contributor_role_fallback(contributors, canonical_roles) -> None:
    raw = complete_v2_descriptor()
    raw["contributors"] = contributors
    result = DataPackage.from_descriptor(raw).to_canonical_descriptor()
    assert result["contributors"][0]["roles"] == canonical_roles


def test_authored_operational_models_use_typed_adapters() -> None:
    spec = TypeSpec(
        fields=[FieldSpec(name="id", type=UniversalType.INTEGER)]
    )
    dialect = TableDialect(delimiter=";")
    package = DataPackage(
        resources=[
            DataResource(
                name="orders",
                path="orders.csv",
                schema=spec,
                dialect=dialect,
            )
        ]
    )
    result = package.to_descriptor()
    assert result["resources"][0]["schema"] == typespec_to_frictionless(spec)
    assert result["resources"][0]["dialect"] == {"delimiter": ";"}


def test_canonical_output_adds_standard_nested_profile_uris() -> None:
    raw = complete_v2_descriptor()
    del raw["$schema"]
    resource = raw["resources"][0]
    del resource["$schema"]
    del resource["schema"]["$schema"]
    del resource["dialect"]["$schema"]
    result = DataPackage.from_descriptor(raw).to_canonical_descriptor()
    assert result["$schema"] == PACKAGE_PROFILE
    assert result["resources"][0]["$schema"] == RESOURCE_PROFILE
    assert result["resources"][0]["schema"]["$schema"] == SCHEMA_PROFILE
    assert result["resources"][0]["dialect"]["$schema"] == DIALECT_PROFILE


def test_canonical_output_does_not_infer_resource_type() -> None:
    result = DataPackage.from_descriptor(
        {"resources": [{"name": "orders", "path": "orders.csv"}]}
    ).to_canonical_descriptor()
    assert "type" not in result["resources"][0]


def test_write_mode_is_the_only_new_top_level_export() -> None:
    assert ma.DescriptorWriteMode is DescriptorWriteMode
    assert not hasattr(ma, "DescriptorError")

def test_raw_resource_tests_use_package_decoder() -> None:
    raw = {"name": "orders", "path": "orders.csv", "futurePropX": 42}
    resource = DataPackage.from_descriptor({"resources": [raw]}).resources[0]
    assert resource.extras == {"futurePropX": 42}


def test_canonical_preserves_nested_profile_extensions() -> None:
    package = DataPackage(
        resources=[
            DataResource(
                name="orders",
                path="orders.csv",
                schema={"profile": {"name": "schema-extension"}, "fields": []},
                dialect={"profile": {"name": "dialect-extension"}},
            )
        ]
    )
    result = package.to_canonical_descriptor()
    assert result["resources"][0]["schema"]["profile"] == {"name": "schema-extension"}
    assert result["resources"][0]["dialect"]["profile"] == {"name": "dialect-extension"}


def test_canonical_preserves_raw_dialect_extension_keys_and_collisions() -> None:
    package = DataPackage(
        resources=[
            DataResource(
                name="orders",
                path="orders.csv",
                dialect={
                    "profile": {"name": "dialect-extension"},
                    "line_terminator": "\\n",
                    "lineTerminator": "\\r\\n",
                },
            )
        ]
    )
    result = package.to_canonical_descriptor()
    dialect = result["resources"][0]["dialect"]
    assert dialect["line_terminator"] == "\\n"
    assert dialect["lineTerminator"] == "\\r\\n"
    assert dialect["profile"] == {"name": "dialect-extension"}


@pytest.mark.parametrize("marker", ["caseSensitiveHeader", "csvddfVersion"])
def test_direct_resource_dialect_v1_markers_are_rejected(marker) -> None:
    with pytest.raises(UnsupportedDescriptorVersion):
        DataResource(
            name="orders",
            path="orders.csv",
            dialect={marker: True},
        )
