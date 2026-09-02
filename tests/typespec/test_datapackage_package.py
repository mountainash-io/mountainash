import pytest
from mountainash.exceptions import (
    InvalidDescriptorStructure,
    UnsupportedDescriptorVersion,
)
from mountainash.typespec.datapackage import DataPackage, DataResource
from mountainash.typespec.spec import (
    FieldSpec,
    ForeignKey,
    ForeignKeyReference,
    TypeSpec,
)
from mountainash.typespec.universal_types import UniversalType


def _r(name: str, **kw) -> DataResource:
    return DataResource(name=name, path=f"{name}.csv", **kw)


def test_minimal_package():
    pkg = DataPackage(resources=[_r("orders")])
    assert len(pkg.resources) == 1


def test_must_have_at_least_one_resource():
    with pytest.raises(ValueError, match="at least one resource"):
        DataPackage(resources=[])


def test_resource_names_must_be_unique():
    with pytest.raises(ValueError, match="duplicate resource name"):
        DataPackage(resources=[_r("orders"), _r("orders")])


def test_extras_preserved():
    raw = {
        "name": "demo",
        "resources": [{"name": "orders", "path": "orders.csv"}],
        "futureProp": "x",
    }
    pkg = DataPackage.from_descriptor(raw)
    assert pkg.extras == {"futureProp": "x"}
    assert pkg.to_descriptor() == raw


def test_dollar_schema_preserved():
    raw = {
        "$schema": "https://datapackage.org/profiles/2.0/datapackage.json",
        "resources": [{"name": "orders", "path": "orders.csv"}],
    }
    pkg = DataPackage.from_descriptor(raw)
    assert pkg.dollar_schema == "https://datapackage.org/profiles/2.0/datapackage.json"
    assert pkg.to_descriptor()["$schema"] == raw["$schema"]


def test_package_owns_wrappers_and_shared_bindings():
    first = DataResource(name="orders", path="orders.csv")
    second = DataResource(name="items", path="items.csv")
    package = DataPackage(resources=[first, second])
    orders, items = package.resources
    assert isinstance(package.resources, tuple)
    assert orders is not first
    assert items is not second
    assert orders._descriptor_context is package._descriptor_context
    assert items._descriptor_context is package._descriptor_context
    names = orders._package_resource_names
    assert names == frozenset({"orders", "items"})
    assert items._package_resource_names is names
    assert orders._invariant_location.descriptor_path == "$.resources[0]"
    assert items._invariant_location.descriptor_path == "$.resources[1]"
    assert first._package_resource_names == frozenset()


def test_two_packages_do_not_rebind_the_same_input_resource():
    source = DataResource(name="orders", path="orders.csv")
    left = DataPackage(resources=[source])
    right = DataPackage(resources=[source])
    assert left.resources[0] is not right.resources[0]
    assert left.resources[0]._descriptor_context is not right.resources[0]._descriptor_context


@pytest.mark.parametrize(
    ("factory", "descriptor_path", "required_form"),
    [
        (lambda: DataPackage(), "$.resources", "non-empty resource sequence"),
        (lambda: DataPackage(resources=[]), "$.resources", "non-empty resource sequence"),
        (lambda: DataPackage(resources=None), "$.resources", "non-empty resource sequence"),
        (lambda: DataPackage(resources="orders.csv"), "$.resources", "non-empty resource sequence"),
        (lambda: DataPackage(resources=[1]), "$.resources[0]", "resource mapping"),
    ],
)
def test_invalid_package_resource_containers_are_structured(
    factory, descriptor_path, required_form
):
    with pytest.raises(InvalidDescriptorStructure) as caught:
        factory()
    assert caught.value.descriptor_path == descriptor_path
    assert caught.value.required_form == required_form


def test_package_marker_scan_precedes_invalid_resource_shape():
    raw = {
        "resources": [
            {"name": "", "path": "orders.csv"},
            {"name": "items", "path": "items.csv", "profile": "v1"},
        ]
    }
    with pytest.raises(UnsupportedDescriptorVersion) as caught:
        DataPackage.from_descriptor(raw)
    assert caught.value.descriptor_path == "$.resources[1].profile"


def test_direct_and_descriptor_package_markers_have_equal_public_fields():
    marker = "https://datapackage.org/profiles/1.0/datapackage.json"
    factories = (
        lambda: DataPackage(
            dollar_schema=marker,
            resources=[{"name": "orders", "path": "orders.csv"}],
        ),
        lambda: DataPackage.from_descriptor(
            {"$schema": marker, "resources": [{"name": "orders", "path": "orders.csv"}]}
        ),
    )
    for factory in factories:
        with pytest.raises(UnsupportedDescriptorVersion) as caught:
            factory()
        assert caught.value.descriptor_path == "$.$schema"
        assert caught.value.rejected_value == marker


def test_package_revalidates_invalid_nested_metadata_for_mapping_and_resource_inputs():
    raw = {
        "name": "orders",
        "data": [],
        "licenses": [{"name": 42}],
    }
    resource = DataResource(name="orders", data=[], licenses=[{"name": 42}])
    for value in (raw, resource):
        with pytest.raises(InvalidDescriptorStructure) as caught:
            DataPackage(resources=[value])
        assert caught.value.descriptor_path == "$.resources[0].licenses[0]"
        assert caught.value.required_form == "valid license object"

def test_package_model_copy_preserves_context_provenance_and_data_identity():
    payload = object()
    package = DataPackage(
        sources=[{"title": "catalog"}],
        resources=[DataResource(name="orders", data=payload)],
    )
    copied = package.model_copy()
    assert copied is not package
    assert copied.resources[0] is not package.resources[0]
    assert copied.resources[0].data is payload
    assert copied._descriptor_context is not package._descriptor_context
    assert copied._descriptor_context.base_uri == package._descriptor_context.base_uri
    assert copied._descriptor_context.resolver is package._descriptor_context.resolver
    assert copied.resources[0]._descriptor_context is copied._descriptor_context
    assert copied.resources[0]._package_resource_names is not package.resources[0]._package_resource_names


def test_package_resources_are_immutable_after_construction():
    package = DataPackage(resources=[_r("orders")])
    with pytest.raises(TypeError, match="resources is immutable"):
        package.resources = ()
    with pytest.raises(ValueError, match="does not support deep=True"):
        package.model_copy(deep=True)


def test_package_revalidates_malformed_foreign_key_at_package_location():
    schema = {
        "fields": [{"name": "id"}],
        "foreignKeys": [
            {"fields": [], "reference": {"resource": "", "fields": ["id"]}}
        ],
    }
    resource = DataResource(name="orders", data=[])
    resource.table_schema = schema
    for value in (
        {"name": "orders", "data": [], "schema": schema},
        resource,
    ):
        with pytest.raises(InvalidDescriptorStructure) as caught:
            DataPackage(resources=[value])
        assert caught.value.descriptor_path == "$.resources[0].schema.foreignKeys[0].fields"


def test_package_accepts_typed_self_reference_none():
    spec = TypeSpec(
        fields=[FieldSpec("id", UniversalType.INTEGER)],
        foreign_keys=[
            ForeignKey(
                fields=["id"],
                reference=ForeignKeyReference(None, ["id"]),
            )
        ],
    )
    package = DataPackage(
        name="p",
        resources=[DataResource(name="r", data=[], schema=spec)],
    )
    assert package.resources[0].to_typespec() == spec
    assert package.resources[0].to_typespec() is not spec
