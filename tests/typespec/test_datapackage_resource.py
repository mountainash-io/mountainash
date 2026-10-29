import json
from collections.abc import Mapping

import pytest

from mountainash.exceptions import (
    DescriptorReferenceInvalid,
    InvalidDescriptorRelationship,
    IncompatibleFieldPropertiesError,
    InvalidDescriptorStructure,
    InvalidFieldMatchDeclaration,
    InvalidKeyShapeError,
    MissingDescriptorBase,
    UnsupportedDescriptorVersion,
    UnsupportedResourceDialect,
)
from mountainash.typespec.datapackage import (
    DataPackage,
    DataResource,
    TableDialect,
    _copy_resource_for_package,
)
from mountainash.typespec.descriptor_context import (
    DescriptorContext,
    DescriptorKind,
    DefaultDescriptorResolver,
)
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.frictionless_invariants import InvariantLocation
from mountainash.typespec.spec import FieldDefinition, TableSchema

VALID_SCHEMA = {"fields": [{"name": "id", "type": "integer"}]}
EXTERNAL_FK_SCHEMA = {
    "fields": [{"name": "customer_id"}],
    "foreignKeys": [
        {
            "fields": ["customer_id"],
            "reference": {"resource": "customers", "fields": ["id"]},
        }
    ],
}

def construct_resource(entrypoint: str, raw: dict[str, object]) -> DataResource:
    if entrypoint == "init":
        return DataResource(**raw)
    if entrypoint == "model_validate":
        return DataResource.model_validate(raw)
    if entrypoint == "model_validate_json":
        return DataResource.model_validate_json(json.dumps(raw))
    raise AssertionError(f"unknown entrypoint: {entrypoint}")


@pytest.mark.parametrize("entrypoint", ["init", "model_validate", "model_validate_json"])
def test_resource_entrypoints_share_source_error(entrypoint: str) -> None:
    raw = {"name": "", "path": "orders.csv"}
    with pytest.raises(InvalidDescriptorStructure) as caught:
        construct_resource(entrypoint, raw)
    assert caught.value.descriptor_path == "$.name"
    assert caught.value.required_form == "non-empty string resource name"


def test_resource_model_copy_is_standalone_and_preserves_data_identity() -> None:
    payload = object()
    package = DataPackage(resources=[DataResource(name="r", data=payload)])
    copied = package.resources[0].model_copy()
    assert copied.data is payload
    assert copied._package_resource_names == frozenset()
    assert copied._descriptor_context.base_uri is None
    assert copied._invariant_location.descriptor_path == "$"


def test_resource_model_copy_rejects_deep_copy() -> None:
    resource = DataResource(name="r", data=object())
    with pytest.raises(ValueError, match="does not support deep=True"):
        resource.model_copy(deep=True)


def test_resource_model_copy_deep_copies_metadata() -> None:
    schema = {"fields": [{"name": "id"}]}
    dialect = {"delimiter": ";"}
    extras = {"nested": [{"value": 1}]}
    resource = DataResource(
        name="r",
        path="orders.csv",
        schema=schema,
        dialect=dialect,
        extras=extras,
        data=None,
    )
    copied = resource.model_copy()
    assert copied.table_schema == schema
    assert copied.table_schema is not resource.table_schema
    assert copied.dialect == dialect
    assert copied.dialect is not resource.dialect
    assert copied.extras == extras
    assert copied.extras is not resource.extras
    copied.extras["nested"][0]["value"] = 2
    assert resource.extras["nested"][0]["value"] == 1


def test_resource_model_copy_deep_copies_typed_declarations() -> None:
    schema = TableSchema(fields={"id": FieldDefinition(type=UniversalType.INTEGER)})
    dialect = TableDialect(delimiter=";")
    resource = DataResource(name="r", data=[], schema=schema, dialect=dialect)
    copied = resource.model_copy()
    assert copied.table_schema == schema
    assert copied.table_schema is not schema
    assert copied.dialect == dialect
    assert copied.dialect is not dialect


def test_resource_name_is_immutable_after_construction() -> None:
    resource = DataResource(name="r", data=object())
    with pytest.raises(TypeError, match="name is immutable"):
        resource.name = "renamed"


def test_resource_model_copy_normalizes_python_field_names() -> None:
    resource = DataResource(name="r", data=object())
    copied = resource.model_copy(
        update={
            "name": "renamed",
            "table_schema": {"fields": [{"name": "id"}]},
            "bytes_": 12,
        }
    )
    assert copied.name == "renamed"
    assert copied.table_schema == {"fields": [{"name": "id"}]}
    assert copied.bytes_ == 12


def test_resource_model_copy_renames_without_mutating_original() -> None:
    payload = object()
    resource = DataResource(
        name="old_name",
        data=payload,
        schema={"fields": [{"name": "id"}]},
    )
    copied = resource.model_copy(update={"name": "new_name"})
    assert copied is not resource
    assert copied.name == "new_name"
    assert copied.data is payload
    assert copied.table_schema == resource.table_schema
    with pytest.raises(TypeError, match="name is immutable"):
        resource.name = "other_name"


@pytest.mark.parametrize("entrypoint", ["init", "model_validate", "model_validate_json"])
def test_resource_entrypoints_reject_malformed_inline_foreign_key(entrypoint: str) -> None:
    raw = {
        "name": "orders",
        "data": [],
        "schema": {
            "fields": [{"name": "id"}],
            "foreignKeys": [
                {
                    "fields": [],
                    "reference": {"resource": "", "fields": ["id"]},
                }
            ],
        },
    }
    with pytest.raises(InvalidDescriptorStructure) as caught:
        construct_resource(entrypoint, raw)
    assert caught.value.descriptor_path == "$.schema.foreignKeys[0].fields"
    assert caught.value.required_form == "field name string or non-empty field name list"


def test_resource_model_validate_preserves_data_identity() -> None:
    payload = object()
    resource = DataResource.model_validate({"name": "r", "data": payload})
    assert resource.data is payload


def test_copy_resource_for_package_binds_supplied_location() -> None:
    payload = object()
    source = DataResource(name="orders", data=payload)
    copied = _copy_resource_for_package(
        source,
        location=InvariantLocation("$.resources[0]", "orders"),
    )
    assert copied is not source
    assert copied.data is payload
    assert copied._invariant_location.descriptor_path == "$.resources[0]"


def test_resource_decoding_stays_at_package_boundary() -> None:
    raw_resource = {"name": "orders", "path": "orders.csv"}
    package = DataPackage.from_descriptor({"resources": [raw_resource]})
    assert not hasattr(DataResource, "from_descriptor")
    assert package.resources[0].to_descriptor() == raw_resource

def test_resource_accepts_raw_schema_and_dialect_references() -> None:
    resource = DataResource(
        name="orders",
        path="orders.csv",
        schema="schema.json",
        dialect="dialect.json",
    )
    assert resource.table_schema == "schema.json"
    assert resource.dialect == "dialect.json"


def test_resource_has_v2_schema_url_and_homepage() -> None:
    resource = DataResource(
        name="orders",
        path="orders.csv",
        schema_url="https://example.com/resource-profile",
        homepage="https://example.com/orders",
    )
    assert resource.schema_url.endswith("resource-profile")
    assert resource.homepage.endswith("/orders")


def test_context_does_not_change_equality() -> None:
    left = DataResource(name="orders", path="orders.csv")
    right = DataResource(name="orders", path="orders.csv")
    right._descriptor_context = DescriptorContext(
        base_uri="file:///tmp/",
        resolver=DefaultDescriptorResolver(),
        package_sources=(),
    )
    right._package_resource_names = frozenset({"orders"})
    assert left == right


def test_effective_sources_returns_a_fresh_list() -> None:
    resource = DataResource(name="orders", path="orders.csv")
    resource._descriptor_context = DescriptorContext(
        base_uri=None,
        resolver=DefaultDescriptorResolver(),
        package_sources=({"title": "catalog"},),
    )
    first = resource.effective_sources
    first[0]["title"] = "changed"
    assert resource.effective_sources == [{"title": "catalog"}]

def test_context_snapshots_nested_package_sources() -> None:
    source = {"title": "catalog", "meta": {"tags": ["a"]}}
    package = DataPackage(
        sources=[source], resources=[DataResource(name="r", path="r.csv")]
    )
    source["meta"]["tags"].append("changed")
    package.sources[0]["meta"]["tags"].append("model-change")
    assert package.resources[0].effective_sources == [
        {"title": "catalog", "meta": {"tags": ["a"]}}
    ]


def test_effective_sources_result_has_no_nested_alias() -> None:
    package = DataPackage(
        sources=[{"meta": {"tags": ["a"]}}],
        resources=[DataResource(name="r", path="r.csv")],
    )
    result = package.resources[0].effective_sources
    result[0]["meta"]["tags"].append("changed")
    assert package.resources[0].effective_sources[0]["meta"]["tags"] == ["a"]


def test_package_model_copy_update_owns_nested_sources() -> None:
    package = DataPackage(
        sources=[{"title": "catalog", "meta": {"tags": ["a"]}}],
        resources=[DataResource(name="r", path="r.csv")],
    )
    update_sources = [{"title": "updated", "meta": {"tags": ["b"]}}]
    copied = package.model_copy(update={"sources": update_sources})
    update_sources[0]["meta"]["tags"].append("caller-change")
    copied.sources[0]["meta"]["tags"].append("model-change")
    assert copied.resources[0].effective_sources == [
        {"title": "updated", "meta": {"tags": ["b"]}}
    ]
    assert package.resources[0].effective_sources == [
        {"title": "catalog", "meta": {"tags": ["a"]}}
    ]

def test_minimal_resource_with_path():
    r = DataResource(name="orders", path="orders.csv")
    assert r.name == "orders"
    assert r.path == "orders.csv"
    assert r.data is None


def test_resource_with_inline_data():
    r = DataResource(name="orders", data=[{"id": 1}, {"id": 2}])
    assert r.data == [{"id": 1}, {"id": 2}]
    assert r.path is None


def test_must_have_exactly_one_of_path_or_data():
    with pytest.raises(InvalidDescriptorStructure, match="invalid resource descriptor structure") as missing:
        DataResource(name="orders")
    assert missing.value.descriptor_path == "$"
    assert missing.value.required_form == "exactly one of path or data"
    with pytest.raises(InvalidDescriptorStructure, match="invalid resource descriptor structure") as both:
        DataResource(name="orders", path="x.csv", data=[{"id": 1}])
    assert both.value.descriptor_path == "$"
    assert both.value.required_form == "exactly one of path or data"

@pytest.mark.parametrize(
    ("payload", "descriptor_path", "required_form"),
    [
        ({"name": "orders"}, "$", "exactly one of path or data"),
        ({"name": "orders", "path": "orders.csv", "data": []}, "$", "exactly one of path or data"),
        ({"name": "orders", "path": []}, "$.path", "non-empty string or non-empty list of strings"),
    ],
)
def test_resource_model_validate_json_uses_source_shape_adapter(
    payload, descriptor_path, required_form
) -> None:
    with pytest.raises(InvalidDescriptorStructure) as caught:
        DataResource.model_validate_json(json.dumps(payload))
    assert caught.value.descriptor_path == descriptor_path
    assert caught.value.required_form == required_form


@pytest.mark.parametrize("marker", ["caseSensitiveHeader", "csvddfVersion"])
def test_resource_model_validate_uses_profile_adapter(marker) -> None:
    with pytest.raises(UnsupportedDescriptorVersion) as caught:
        DataResource.model_validate(
            {"name": "orders", "path": "orders.csv", "dialect": {marker: True}}
        )
    assert caught.value.descriptor_path == f"$.dialect.{marker}"



def test_resource_model_validate_uses_source_shape_adapter() -> None:
    with pytest.raises(InvalidDescriptorStructure) as caught:
        DataResource.model_validate({"name": "orders", "path": []})
    assert caught.value.descriptor_path == "$.path"
    assert caught.value.required_form == "non-empty string or non-empty list of strings"

def test_multi_file_path_array():
    r = DataResource(name="orders", path=["a.csv", "b.csv"])
    assert r.path == ["a.csv", "b.csv"]


def test_extras_preserved():
    raw = {"name": "orders", "path": "orders.csv", "futurePropX": 42}
    r = DataPackage.from_descriptor({"resources": [raw]}).resources[0]
    assert r.extras == {"futurePropX": 42}
    assert r.to_descriptor() == raw


def test_dialect_round_trip():
    raw = {
        "name": "orders",
        "path": "orders.csv",
        "type": "table",
        "dialect": {"delimiter": ";"},
    }
    r = DataPackage.from_descriptor({"resources": [raw]}).resources[0]
    assert r.dialect == raw["dialect"]
    assert r.to_descriptor() == raw


def test_descriptor_owns_raw_mapping_values() -> None:
    dialect = {"dialect": {"delimiter": ";"}}
    schema = {"fields": [{"name": "id"}]}
    resource = DataResource(
        name="orders",
        path="orders.csv",
        dialect=dialect,
        schema=schema,
    )
    descriptor = resource.to_descriptor()
    descriptor["dialect"]["dialect"]["delimiter"] = "|"
    descriptor["schema"]["fields"][0]["name"] = "order_id"
    assert resource.dialect == dialect
    assert resource.table_schema == schema



def test_to_table_schema_none_when_no_schema():
    r = DataResource(name="t", path="t.csv")
    assert r.to_table_schema() is None


def test_to_table_schema_passthrough_when_already_typed():
    spec = TableSchema(fields={"id": FieldDefinition(type=UniversalType.INTEGER)})
    r = DataResource(name="t", path="t.csv", schema=spec)
    assert r.to_table_schema() is spec




def test_to_table_schema_converts_raw_dict():
    r = DataResource(
        name="t", path="t.csv",
        schema={"fields": [{"name": "id", "type": "integer"}]},
    )
    spec = r.to_table_schema()
    assert spec.field_names == ["id"]
    assert spec.get_field("id").type == UniversalType.INTEGER


def test_to_typespec_raises_on_garbage_schema():
    r = DataResource(name="t", path="t.csv", schema="garbage")
    with pytest.raises(MissingDescriptorBase):
        r.to_table_schema()


def test_inline_wrong_schema_kind_stays_structural_error() -> None:
    resource = DataResource(
        name="orders",
        path="orders.csv",
        schema={"resources": []},
    )
    with pytest.raises(InvalidDescriptorStructure):
        resource.to_table_schema()


@pytest.mark.parametrize(
    "schema,error_type",
    [
        (
            {"fields": [], "fieldsMatch": "open"},
            InvalidFieldMatchDeclaration,
        ),
        (
            {"fields": [{"name": "x", "type": "string", "itemType": "integer"}]},
            IncompatibleFieldPropertiesError,
        ),
        (
            {"fields": [], "primaryKey": {"id"}},
            InvalidKeyShapeError,
        ),
    ],
)
def test_to_typespec_preserves_typespec_errors(schema, error_type) -> None:
    resource = DataResource(name="r", data=[], schema=schema)
    with pytest.raises(error_type):
        resource.to_table_schema()



def test_to_contract_raises_when_no_schema():
    r = DataResource(name="t", path="t.csv")
    with pytest.raises(ValueError, match="table_schema"):
        r.to_contract()


def test_resource_contract_enforces_inline_constraints():
    import polars as pl

    resource = DataResource(
        name="t",
        path="t.csv",
        schema={
            "fields": [
                {"name": "id", "type": "integer", "constraints": {"minimum": 0}}
            ],
            "primaryKey": ["id"],
        },
    )
    result = resource.to_contract().validate_datacontract(
        pl.DataFrame({"id": [-1, 1]})
    )
    assert not result.passes
    assert result.failure_cases.get_column("id").to_list() == [-1]


def test_to_dialect_none_when_no_dialect() -> None:
    resource = DataResource(name="orders", path="orders.csv")
    assert resource.to_dialect() is None


def test_to_dialect_passthrough_when_already_table_dialect() -> None:
    dialect = TableDialect(delimiter=";")
    resource = DataResource(name="orders", path="orders.csv", dialect=dialect)
    assert resource.to_dialect() is dialect


def test_to_dialect_converts_raw_mapping() -> None:
    resource = DataResource(
        name="orders",
        path="orders.csv",
        format="csv",
        dialect={"delimiter": ";"},
    )
    assert resource.to_dialect().delimiter == ";"


def test_to_dialect_rejects_mixed_exclusive_families() -> None:
    resource = DataResource(
        name="orders",
        path="orders.csv",
        dialect={"delimiter": ";", "property": "items"},
    )
    with pytest.raises(UnsupportedResourceDialect):
        resource.to_dialect()
def test_to_dialect_rejects_incompatible_resource_format_family() -> None:
    resource = DataResource(
        name="orders",
        path="orders.csv",
        format="csv",
        dialect={"property": "items"},
    )
    with pytest.raises(UnsupportedResourceDialect):
        resource.to_dialect()




def descriptor_with_references() -> dict[str, object]:
    return {
        "resources": [
            {
                "name": "orders",
                "path": "orders.csv",
                "schema": "schema.json",
                "dialect": "dialect.json",
            }
        ]
    }


class RecordingResolver:
    def __init__(self, documents: dict[str, dict[str, object]]) -> None:
        self.documents = documents
        self.calls: list[tuple[str, DescriptorKind]] = []

    def resolve(self, reference, *, base_uri, expected_kind):
        self.calls.append((reference, expected_kind))
        return dict(self.documents[reference])


@pytest.mark.parametrize("referenced", [False, True])
def test_resource_retains_nested_codec_error_path_without_rewriting_raw(referenced):
    schema = {
        "fields": [{
            "name": "payload",
            "type": "object",
            "x-mountainash": {
                "fields": [
                    {"name": "a.b", "type": "integer"},
                    {"name": "a.b", "type": "integer"},
                ]
            },
        }]
    }
    raw = {
        "resources": [{
            "name": "records",
            "path": "records.csv",
            "schema": "schema.json" if referenced else schema,
        }]
    }
    resolver = RecordingResolver({"schema.json": schema})
    package = DataPackage.from_descriptor(
        raw, base_uri="file:///tmp/", resolver=resolver
    )
    assert package.to_descriptor() == raw
    error_type = DescriptorReferenceInvalid if referenced else InvalidDescriptorStructure
    with pytest.raises(error_type) as caught:
        package.resources[0].to_table_schema()
    suffix = ".fields[0].x-mountainash.fields[1].name"
    prefix = "$.resources[0].schema" if referenced else "$"
    assert caught.value.descriptor_path == prefix + suffix
    if referenced:
        assert isinstance(caught.value.__cause__, InvalidDescriptorStructure)
        assert caught.value.__cause__.descriptor_path == "$" + suffix
    assert resolver.calls == (
        [("schema.json", DescriptorKind.SCHEMA)] if referenced else []
    )
    assert package.to_descriptor() == raw


class SingleDocumentResolver:
    def __init__(self, document: Mapping[str, object]) -> None:
        self.document = document
        self.calls: list[tuple[str, DescriptorKind]] = []

    def resolve(self, reference, *, base_uri, expected_kind):
        self.calls.append((reference, expected_kind))
        return dict(self.document)


class RaisingResolver:
    def resolve(self, reference, *, base_uri, expected_kind):
        raise PermissionError(reference)


def test_referenced_schema_is_resolved_once_per_relationship_access():
    resolver = RecordingResolver({"schema.json": VALID_SCHEMA})
    resource = DataPackage.from_descriptor(
        {"resources": [{"name": "orders", "path": "orders.csv", "schema": "schema.json"}]},
        base_uri="file:///tmp/",
        resolver=resolver,
    ).resources[0]
    assert resource._validated_foreign_keys() == ()
    assert resolver.calls == [("schema.json", DescriptorKind.SCHEMA)]


def test_to_typespec_resolves_referenced_schema_once():
    resolver = RecordingResolver({"schema.json": VALID_SCHEMA})
    resource = DataPackage.from_descriptor(
        {"resources": [{"name": "orders", "path": "orders.csv", "schema": "schema.json"}]},
        base_uri="file:///tmp/",
        resolver=resolver,
    ).resources[0]
    assert resource.to_table_schema().field_names == ["id"]
    assert resolver.calls == [("schema.json", DescriptorKind.SCHEMA)]


def test_standalone_external_target_fails_at_schema_location():
    resource = DataResource(name="child", data=[], schema=EXTERNAL_FK_SCHEMA)
    with pytest.raises(InvalidDescriptorRelationship) as caught:
        resource.to_table_schema()
    assert caught.value.descriptor_path == "$.schema.foreignKeys[0].reference.resource"


def test_resolver_transport_failure_is_typed_with_cause() -> None:
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": "schema.json",
                }
            ]
        },
        resolver=RaisingResolver(),
    ).resources[0]

    with pytest.raises(DescriptorReferenceInvalid) as caught:
        resource.to_table_schema()
    assert isinstance(caught.value.__cause__, PermissionError)




def test_schema_and_dialect_resolution_is_lazy_and_one_hop() -> None:
    resolver = RecordingResolver({
        "schema.json": {"fields": [{"name": "id", "type": "integer"}]},
        "dialect.json": {"delimiter": ";"},
    })
    package = DataPackage.from_descriptor(
        descriptor_with_references(),
        base_uri="file:///tmp/descriptors/",
        resolver=resolver,
    )
    assert resolver.calls == []
    assert package.resources[0].to_table_schema().field_names == ["id"]
    assert package.resources[0].to_dialect().delimiter == ";"
    assert resolver.calls == [
        ("schema.json", DescriptorKind.SCHEMA),
        ("dialect.json", DescriptorKind.DIALECT),
    ]


def test_inline_accessors_do_not_resolve_or_mutate_mapping() -> None:
    schema = {"fields": [{"name": "id", "type": "integer"}]}
    dialect = {"delimiter": ";"}
    resolver = RecordingResolver({})
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": schema,
                    "dialect": dialect,
                }
            ]
        },
        resolver=resolver,
    ).resources[0]

    assert resource.to_table_schema().field_names == ["id"]
    assert resource.to_dialect().delimiter == ";"
    assert resolver.calls == []
    assert schema == {"fields": [{"name": "id", "type": "integer"}]}
    assert dialect == {"delimiter": ";"}


@pytest.mark.parametrize(
    ("kind", "document", "accessor"),
    [
        (DescriptorKind.SCHEMA, {}, "to_table_schema"),
        (DescriptorKind.SCHEMA, {"resources": []}, "to_table_schema"),
        (DescriptorKind.DIALECT, {"fields": []}, "to_dialect"),
        (DescriptorKind.DIALECT, {"resources": []}, "to_dialect"),
        (DescriptorKind.DIALECT, {}, "to_dialect"),
    ],
)
def test_resolved_documents_must_match_expected_kind(
    kind: DescriptorKind,
    document: dict[str, object],
    accessor: str,
) -> None:
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": "schema.json" if kind is DescriptorKind.SCHEMA else {"fields": []},
                    "dialect": "dialect.json" if kind is DescriptorKind.DIALECT else {"delimiter": ";"},
                }
            ]
        },
        resolver=SingleDocumentResolver(document),
    ).resources[0]
    with pytest.raises(DescriptorReferenceInvalid):
        getattr(resource, accessor)()


@pytest.mark.parametrize(
    ("reference", "expected_kind", "document", "accessor"),
    [
        (
            "schema.json",
            DescriptorKind.SCHEMA,
            {
                "fields": [{"name": "id"}],
                "$schema": "https://specs.frictionlessdata.io/schemas/table-schema.json",
            },
            "to_table_schema",
        ),
        (
            "dialect.json",
            DescriptorKind.DIALECT,
            {
                "delimiter": ";",
                "$schema": "https://specs.frictionlessdata.io/schemas/csv-dialect.json",
            },
            "to_dialect",
        ),
    ],
)
def test_resolved_documents_reject_v1_markers(
    reference: str,
    expected_kind: DescriptorKind,
    document: dict[str, object],
    accessor: str,
) -> None:
    resolver = SingleDocumentResolver(document)
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": reference if expected_kind is DescriptorKind.SCHEMA else {"fields": []},
                    "dialect": reference if expected_kind is DescriptorKind.DIALECT else {"delimiter": ";"},
                }
            ]
        },
        resolver=resolver,
    ).resources[0]
    with pytest.raises(UnsupportedDescriptorVersion):
        getattr(resource, accessor)()
    assert len(resolver.calls) == 1


def test_resolved_unknown_schema_profile_is_allowed() -> None:
    resolver = SingleDocumentResolver(
        {
            "fields": [{"name": "id"}],
            "profile": "https://example.com/custom-profile",
        }
    )
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": "schema.json",
                }
            ]
        },
        resolver=resolver,
    ).resources[0]

    assert resource.to_table_schema().field_names == ["id"]


def test_resolved_unknown_dialect_profile_is_allowed() -> None:
    resolver = SingleDocumentResolver(
        {
            "delimiter": ";",
            "profile": "https://example.com/custom-profile",
        }
    )
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "dialect": "dialect.json",
                }
            ]
        },
        resolver=resolver,
    ).resources[0]

    assert resource.to_dialect().delimiter == ";"


def test_resolved_invalid_dialect_shape_is_typed_with_cause() -> None:
    resolver = SingleDocumentResolver({"header": {}})
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "dialect": "dialect.json",
                }
            ]
        },
        resolver=resolver,
    ).resources[0]

    with pytest.raises(DescriptorReferenceInvalid) as caught:
        resource.to_dialect()
    assert caught.value.__cause__ is not None


def test_resolved_invalid_foreign_key_shape_raises_typed_key_shape_error() -> None:
    # An invalid FK key shape resolved from a reference string is a typed
    # structural error (InvalidKeyShapeError / TypeSpecError) and passes
    # through unchanged — it is NOT rewrapped as a descriptor error
    # (Section 10 / Section 12.1 boundary rule).
    resolver = SingleDocumentResolver(
        {
            "fields": [{"name": "customer_id"}],
            "foreignKeys": [
                {
                    "fields": 1,
                    "reference": {"resource": "", "fields": ["id"]},
                }
            ],
        }
    )
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": "schema.json",
                }
            ]
        },
        resolver=resolver,
    ).resources[0]

    with pytest.raises(InvalidKeyShapeError) as caught:
        resource.to_table_schema()
    assert caught.value.field_name == "foreign_key.fields"


@pytest.mark.parametrize(
    ("reference", "expected_kind", "nested_key", "accessor"),
    [
        ("schema.json", DescriptorKind.SCHEMA, "schema", "to_table_schema"),
        ("dialect.json", DescriptorKind.DIALECT, "dialect", "to_dialect"),
    ],
)
def test_resolved_nested_reference_is_rejected_without_second_call(
    reference: str,
    expected_kind: DescriptorKind,
    nested_key: str,
    accessor: str,
) -> None:
    resolver = RecordingResolver({
        reference: {
            "fields": [{"name": "id"}],
            "delimiter": ";",
            nested_key: "nested.json",
        }
    })
    resource = DataPackage.from_descriptor(
        {
            "resources": [
                {
                    "name": "orders",
                    "path": "orders.csv",
                    "schema": reference if expected_kind is DescriptorKind.SCHEMA else {"fields": []},
                    "dialect": reference if expected_kind is DescriptorKind.DIALECT else {"delimiter": ";"},
                }
            ]
        },
        resolver=resolver,
    ).resources[0]
    with pytest.raises(DescriptorReferenceInvalid):
        getattr(resource, accessor)()
    assert resolver.calls == [(reference, expected_kind)]


@pytest.mark.parametrize("loader", ["from_descriptor", "from_json", "from_path"])
def test_loader_policy_intent_survives_storage_binding(tmp_path, loader):
    from mountainash import ResourceRef
    from mountainash_transport.location import LocationNotAllowed, LocationPolicy
    from mountainash_transport.settings.storage.profiles import LocalStorageProfile

    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_bytes(b"v\n9\n")
    raw = {"resources": [{"name": "r", "path": str(outside), "format": "csv"}]}
    descriptor = root / "datapackage.json"
    descriptor.write_text(json.dumps(raw))
    value = {"from_descriptor": raw, "from_json": json.dumps(raw), "from_path": descriptor}[loader]
    load = getattr(DataPackage, loader)
    profile = LocalStorageProfile(ROOT_PATH=str(root), LOCATION_POLICY={})

    inherited = load(value).with_storage(profile)
    with pytest.raises(LocationNotAllowed):
        ResourceRef(inherited.resources[0]).read_bytes()
    explicit_off = load(value, policy=None).with_storage(profile)
    assert ResourceRef(explicit_off.resources[0]).read_bytes() == b"v\n9\n"
    replaced = inherited.with_storage(profile, policy=LocationPolicy(root=str(tmp_path)))
    assert ResourceRef(replaced.resources[0]).read_bytes() == b"v\n9\n"
    assert explicit_off.to_descriptor() == raw


def test_rebinding_recalculates_inherited_policy_but_retains_explicit_off(tmp_path):
    from mountainash import ResourceRef
    from mountainash_transport.location import LocationNotAllowed
    from mountainash_transport.settings.storage.profiles import LocalStorageProfile

    roots = [tmp_path / name for name in ("a", "b")]
    for root in roots:
        root.mkdir()
    source = roots[1] / "rows.csv"
    source.write_bytes(b"v\n91\n")
    profiles = [LocalStorageProfile(ROOT_PATH=str(root), LOCATION_POLICY={}) for root in roots]
    raw = {"resources": [{"name": "r", "path": str(source), "format": "csv"}]}
    original = DataPackage.from_descriptor(raw).with_storage(profiles[0])
    with pytest.raises(LocationNotAllowed):
        ResourceRef(original.resources[0]).read_bytes()
    rebound = original.with_storage(profiles[1])
    assert ResourceRef(rebound.resources[0]).read_bytes() == b"v\n91\n"
    off = original.with_storage(profiles[0], policy=None).with_storage(profiles[0])
    assert ResourceRef(off.resources[0]).read_bytes() == b"v\n91\n"
    assert original.to_descriptor() == rebound.to_descriptor() == off.to_descriptor() == raw


@pytest.mark.parametrize("copy_kind", ["resource-copy", "resource-validate", "package-init", "package-copy", "package-validate", "mapping-validate"])
def test_bound_resource_copies_keep_distinct_sources(tmp_path, copy_kind):
    from mountainash import ResourceRef
    from mountainash_transport.settings.storage.profiles import LocalStorageProfile

    resources = []
    for name, value in (("a", 11), ("b", 91)):
        root = tmp_path / name
        root.mkdir()
        (root / "rows.csv").write_text(f"v\n{value}\n")
        resources.append(DataResource(name=name, path="rows.csv", format="csv").with_storage(
            LocalStorageProfile(ROOT_PATH=str(root)),
        ))
    raw = {"resources": [{"name": name, "path": "rows.csv", "format": "csv"} for name in ("a", "b")]}
    package = DataPackage(resources=resources)
    if copy_kind == "resource-copy":
        copied = [r.model_copy() for r in resources]
    elif copy_kind == "resource-validate":
        copied = [DataResource.model_validate(r) for r in resources]
    elif copy_kind == "package-init":
        copied = package.resources
    elif copy_kind == "package-copy":
        copied = package.model_copy().resources
    elif copy_kind == "package-validate":
        copied = DataPackage.model_validate(package).resources
    else:
        copied = DataPackage.model_validate({"resources": resources}).resources
    assert [ResourceRef(r).read_bytes() for r in copied] == [b"v\n11\n", b"v\n91\n"]
    assert package.to_descriptor() == raw
    assert [r.to_descriptor() for r in resources] == raw["resources"]


def test_package_rebinding_preserves_explicit_resource_binding(tmp_path):
    from mountainash import ResourceRef
    from mountainash_transport.settings.storage.profiles import LocalStorageProfile

    profiles = []
    for name, value in (("a", 11), ("b", 91), ("c", 31)):
        root = tmp_path / name
        root.mkdir()
        (root / "rows.csv").write_text(f"v\n{value}\n")
        profiles.append(LocalStorageProfile(ROOT_PATH=str(root)))
    package = DataPackage(resources=[
        DataResource(name="inherited", path="rows.csv", format="csv"),
        DataResource(name="explicit", path="rows.csv", format="csv").with_storage(profiles[1]),
    ]).with_storage(profiles[0])
    rebound = package.with_storage(profiles[2])
    assert [ResourceRef(r).read_bytes() for r in package.resources] == [b"v\n11\n", b"v\n91\n"]
    assert [ResourceRef(r).read_bytes() for r in rebound.resources] == [b"v\n31\n", b"v\n91\n"]
    assert rebound.to_descriptor() == package.to_descriptor()


def test_unconfined_loader_and_relative_profile_roots_anchor_once(tmp_path, monkeypatch):
    from mountainash import ResourceRef
    from mountainash_transport.settings.storage.profiles import LocalStorageProfile

    first = tmp_path / "first"
    second = tmp_path / "second"
    for root, value in ((first, 11), (second, 91)):
        root.mkdir()
        (root / "rows.csv").write_text(f"v\n{value}\n")
        (root / "data").mkdir()
        (root / "data" / "rows.csv").write_text(f"v\n{value + 1}\n")
    monkeypatch.chdir(first)
    loaded = DataPackage.from_descriptor({"resources": [
        {"name": "r", "path": "rows.csv", "format": "csv"},
    ]}, policy=None)
    bound = DataResource(name="bound", path="rows.csv", format="csv").with_storage(
        LocalStorageProfile(ROOT_PATH="data"),
    )
    monkeypatch.chdir(second)
    assert ResourceRef(loaded.resources[0]).read_bytes() == b"v\n11\n"
    assert ResourceRef(bound).read_bytes() == b"v\n12\n"


def test_descriptor_base_is_not_retargeted_by_profile_or_policy_root(tmp_path):
    from mountainash import ResourceRef
    from mountainash_transport.location import LocationPolicy
    from mountainash_transport.settings.storage.profiles import LocalStorageProfile

    declared = tmp_path / "declared"
    profile_root = tmp_path / "profile"
    for root, value in ((declared, 11), (profile_root, 91)):
        root.mkdir()
        (root / "rows.csv").write_text(f"v\n{value}\n")
    package = DataPackage.from_descriptor({"resources": [
        {"name": "r", "path": "rows.csv", "format": "csv"},
    ]}, base_uri=declared, policy=LocationPolicy(root=str(tmp_path))).with_storage(
        LocalStorageProfile(ROOT_PATH=str(profile_root)),
    )
    assert ResourceRef(package.resources[0]).read_bytes() == b"v\n11\n"


@pytest.mark.parametrize("build", ["copy-update", "model-validate"])
def test_bound_resource_in_package_inherits_package_base(tmp_path, build):
    from mountainash import ResourceRef
    from mountainash_transport.settings.storage.profiles import HTTPStorageProfile

    (tmp_path / "orders.csv").write_bytes(b"id\n1\n")
    (tmp_path / "schema.json").write_text('{"fields": [{"name": "id", "type": "integer"}]}')
    (tmp_path / "dialect.json").write_text('{"delimiter": ";"}')
    package = DataPackage.from_descriptor({"resources": [
        {"name": "orders", "path": "orders.csv", "format": "csv", "schema": "schema.json"},
    ]}, base_uri=tmp_path)
    assert ResourceRef(package.resources[0]).read_bytes() == b"id\n1\n"
    bound = DataResource(
        name="orders", path="orders.csv", format="csv", schema="schema.json", dialect="dialect.json",
    ).with_storage(HTTPStorageProfile())
    if build == "copy-update":
        rebuilt = package.model_copy(update={"resources": [bound]})
    else:
        rebuilt = DataPackage.model_validate(package.model_copy(update={"resources": [bound]}))
    resource = rebuilt.resources[0]
    assert ResourceRef(resource).read_bytes() == b"id\n1\n"
    assert resource.to_table_schema().field_names == ["id"]
    assert resource.to_dialect().delimiter == ";"


def test_bound_resource_inherits_package_load_time_cwd(tmp_path, monkeypatch):
    from mountainash import ResourceRef
    from mountainash_transport.settings.storage.profiles import HTTPStorageProfile

    for name, value in (("loaded", 11), ("later", 91)):
        (tmp_path / name).mkdir()
        (tmp_path / name / "rows.csv").write_text(f"v\n{value}\n")
    monkeypatch.chdir(tmp_path / "loaded")
    package = DataPackage.from_descriptor(
        {"resources": [{"name": "r", "path": "rows.csv", "format": "csv"}]},
    )
    bound = DataResource(name="r", path="rows.csv", format="csv").with_storage(HTTPStorageProfile())
    rebuilt = package.model_copy(update={"resources": [bound]})
    monkeypatch.chdir(tmp_path / "later")
    assert ResourceRef(rebuilt.resources[0]).read_bytes() == b"v\n11\n"


def test_explicit_resource_base_is_kept_over_package_base(tmp_path):
    from mountainash import ResourceRef

    for name, value in (("own", 11), ("pkg", 91)):
        (tmp_path / name).mkdir()
        (tmp_path / name / "rows.csv").write_text(f"v\n{value}\n")
    explicit = DataPackage.from_descriptor(
        {"resources": [{"name": "r", "path": "rows.csv", "format": "csv"}]},
        base_uri=tmp_path / "own",
    ).resources[0]
    package = DataPackage.from_descriptor(
        {"resources": [{"name": "original", "path": "rows.csv", "format": "csv"}]},
        base_uri=tmp_path / "pkg",
    )
    rebuilt = package.model_copy(update={"resources": [explicit]})
    assert ResourceRef(rebuilt.resources[0]).read_bytes() == b"v\n11\n"


def test_binding_does_not_read_data_or_trust_descriptor_settings(tmp_path):
    from mountainash import ResourceRef
    from mountainash_transport.settings.storage.profiles import LocalStorageProfile

    raw = {"resources": [{
        "name": "r", "path": "later.csv", "format": "csv",
        "storage_profile": {"ROOT_PATH": "/not-a-runtime-binding"},
    }]}
    original = DataPackage.from_descriptor(raw, base_uri=tmp_path)
    bound = original.with_storage(LocalStorageProfile(ROOT_PATH=str(tmp_path)))
    (tmp_path / "later.csv").write_bytes(b"v\n7\n")
    assert ResourceRef(bound.resources[0]).read_bytes() == b"v\n7\n"
    assert original.to_descriptor() == bound.to_descriptor() == raw