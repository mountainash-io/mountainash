from copy import deepcopy
import json

import pytest

from mountainash.exceptions import (
    InvalidDescriptorStructure,
    InvalidDescriptorSyntax,
    InvalidDescriptorRelationship,
    UnsupportedDescriptorVersion,
    UnsupportedResourceDialect,
)
from mountainash.typespec.datapackage import DataPackage


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


def test_decode_does_not_mutate_input() -> None:
    raw = minimal_descriptor()
    expected = deepcopy(raw)
    DataPackage.from_descriptor(raw)
    assert raw == expected


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
        {"name": "orders", "path": ["a.csv", "b.csv"], "data": None},
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


def test_resource_decoder_is_removed() -> None:
    from mountainash.typespec.datapackage import DataResource

    assert not hasattr(DataResource, "from_descriptor")


def test_raw_resource_tests_use_package_decoder() -> None:
    raw = {"name": "orders", "path": "orders.csv", "futurePropX": 42}
    resource = DataPackage.from_descriptor({"resources": [raw]}).resources[0]
    assert resource.extras == {"futurePropX": 42}
