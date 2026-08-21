from collections.abc import Mapping

import pytest

from mountainash.exceptions import (
    DescriptorReferenceInvalid,
    InvalidDescriptorRelationship,
    InvalidDescriptorStructure,
    MissingDescriptorBase,
    UnsupportedDescriptorVersion,
    UnsupportedResourceDialect,
)
from mountainash.typespec.datapackage import DataPackage, DataResource, TableDialect
from mountainash.typespec.descriptor_context import (
    DescriptorContext,
    DescriptorKind,
    LocalDescriptorResolver,
)
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType


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
    with pytest.raises(ValueError, match="exactly one of path or data"):
        DataResource(name="orders")
    with pytest.raises(ValueError, match="exactly one of path or data"):
        DataResource(name="orders", path="x.csv", data=[{"id": 1}])


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
    with pytest.raises((InvalidDescriptorStructure, DescriptorReferenceInvalid)):
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
    with pytest.raises((InvalidDescriptorStructure, DescriptorReferenceInvalid)):
        getattr(resource, accessor)()
    assert resolver.calls == [(reference, expected_kind)]