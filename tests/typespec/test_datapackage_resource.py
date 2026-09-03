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
    LocalDescriptorResolver,
)
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.frictionless_invariants import InvariantLocation
from mountainash.typespec.spec import FieldSpec, TypeSpec

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
    schema = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
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
        resolver=LocalDescriptorResolver(),
        package_sources=(),
    )
    right._package_resource_names = frozenset({"orders"})
    assert left == right


def test_effective_sources_returns_a_fresh_list() -> None:
    resource = DataResource(name="orders", path="orders.csv")
    resource._descriptor_context = DescriptorContext(
        base_uri=None,
        resolver=LocalDescriptorResolver(),
        package_sources=({"title": "catalog"},),
    )
    first = resource.effective_sources
    first[0]["title"] = "changed"
    assert resource.effective_sources == [{"title": "catalog"}]


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



def test_to_typespec_none_when_no_schema():
    r = DataResource(name="t", path="t.csv")
    assert r.to_typespec() is None


def test_to_typespec_passthrough_when_already_typespec():
    spec = TypeSpec(fields=[FieldSpec(name="id", type=UniversalType.INTEGER)])
    r = DataResource(name="t", path="t.csv", schema=spec)
    assert r.to_typespec() is spec




def test_to_typespec_converts_raw_dict():
    r = DataResource(
        name="t", path="t.csv",
        schema={"fields": [{"name": "id", "type": "integer"}]},
    )
    spec = r.to_typespec()
    assert spec.field_names == ["id"]
    assert spec.get_field("id").type == UniversalType.INTEGER


def test_to_typespec_raises_on_garbage_schema():
    r = DataResource(name="t", path="t.csv", schema="garbage")
    with pytest.raises(MissingDescriptorBase):
        r.to_typespec()


def test_inline_wrong_schema_kind_stays_structural_error() -> None:
    resource = DataResource(
        name="orders",
        path="orders.csv",
        schema={"resources": []},
    )
    with pytest.raises(InvalidDescriptorStructure):
        resource.to_typespec()


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
        resource.to_typespec()



def test_to_contract_raises_when_no_schema():
    r = DataResource(name="t", path="t.csv")
    with pytest.raises(ValueError, match="table_schema"):
        r.to_contract()


def test_to_contract_delegates_to_typespec():
    r = DataResource(
        name="t", path="t.csv",
        schema={"fields": [{"name": "id", "type": "integer"}]},
    )
    assert r.to_contract().to_typespec().fields == r.to_typespec().fields


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
    assert resource.to_typespec().field_names == ["id"]
    assert resolver.calls == [("schema.json", DescriptorKind.SCHEMA)]


def test_standalone_external_target_fails_at_schema_location():
    resource = DataResource(name="child", data=[], schema=EXTERNAL_FK_SCHEMA)
    with pytest.raises(InvalidDescriptorRelationship) as caught:
        resource.to_typespec()
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
        resource.to_typespec()
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
    assert package.resources[0].to_typespec().field_names == ["id"]
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

    assert resource.to_typespec().field_names == ["id"]
    assert resource.to_dialect().delimiter == ";"
    assert resolver.calls == []
    assert schema == {"fields": [{"name": "id", "type": "integer"}]}
    assert dialect == {"delimiter": ";"}


@pytest.mark.parametrize(
    ("kind", "document", "accessor"),
    [
        (DescriptorKind.SCHEMA, {}, "to_typespec"),
        (DescriptorKind.SCHEMA, {"resources": []}, "to_typespec"),
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
            "to_typespec",
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

    assert resource.to_typespec().field_names == ["id"]


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
        resource.to_typespec()
    assert caught.value.field_name == "foreign_key.fields"


@pytest.mark.parametrize(
    ("reference", "expected_kind", "nested_key", "accessor"),
    [
        ("schema.json", DescriptorKind.SCHEMA, "schema", "to_typespec"),
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