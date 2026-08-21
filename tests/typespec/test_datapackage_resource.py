import pytest

from mountainash.typespec.datapackage import DataResource
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType

from mountainash.typespec.descriptor_context import (
    DescriptorContext,
    LocalDescriptorResolver,
)


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
    r = DataResource.from_descriptor(raw)
    assert r.extras == {"futurePropX": 42}
    assert r.to_descriptor() == raw


def test_dialect_round_trip():
    raw = {
        "name": "orders",
        "path": "orders.csv",
        "type": "table",
        "dialect": {"delimiter": ";"},
    }
    r = DataResource.from_descriptor(raw)
    assert r.dialect == raw["dialect"]
    assert r.to_descriptor() == raw



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
    with pytest.raises(TypeError, match="table_schema"):
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