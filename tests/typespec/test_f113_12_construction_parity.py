from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

import polars as pl
import pytest

from mountainash.exceptions import (
    DescriptorReferenceInvalid,
    DescriptorReferenceNotFound,
    DescriptorReferenceSchemeDenied,
    InvalidDescriptorRelationship,
    InvalidDescriptorStructure,
    InvalidDescriptorSyntax,
    MissingDescriptorBase,
    UnsupportedDescriptorVersion,
)
from mountainash.typespec.datapackage import DataPackage, DataResource
from mountainash.typespec.spec import FieldSpec, ForeignKey, ForeignKeyReference, TypeSpec
from mountainash.typespec.universal_types import UniversalType


VALID_CHILD_PARENT_PACKAGE = {
    "name": "context-fixture",
    "sources": [{"title": "catalog", "meta": {"owners": ["data"]}}],
    "resources": [
        {
            "name": "parent",
            "data": [{"id": 1}],
            "type": "table",
            "schema": {"fields": [{"name": "id", "type": "integer"}]},
        },
        {
            "name": "child",
            "data": [{"id": 10, "parent_id": 1}],
            "type": "table",
            "schema": {
                "fields": [
                    {"name": "id", "type": "integer"},
                    {"name": "parent_id", "type": "integer"},
                ],
                "foreignKeys": [
                    {
                        "fields": ["parent_id"],
                        "reference": {"resource": "parent", "fields": ["id"]},
                    }
                ],
            },
        },
    ],
}


PACKAGE_ENTRYPOINTS = (
    lambda raw: DataPackage(**raw),
    lambda raw: DataPackage.model_validate(raw),
    lambda raw: DataPackage.model_validate_json(json.dumps(raw)),
    lambda raw: DataPackage.from_descriptor(raw),
    lambda raw: DataPackage.from_json(json.dumps(raw)),
)


def _assert_error_fields(
    caught: pytest.ExceptionInfo[Exception],
    *,
    error_type: type[Exception],
    descriptor_kind: str,
    descriptor_path: str,
    resource_name: str | None,
    reference: str | None,
    normalized_reference: str | None,
    expected_kind: str | None,
    rejected_value: object,
    required_form: str,
) -> None:
    error = caught.value
    assert type(error) is error_type
    assert error.descriptor_kind == descriptor_kind  # type: ignore[attr-defined]
    assert error.descriptor_path == descriptor_path  # type: ignore[attr-defined]
    assert error.resource_name == resource_name  # type: ignore[attr-defined]
    assert error.reference == reference  # type: ignore[attr-defined]
    assert error.normalized_reference == normalized_reference  # type: ignore[attr-defined]
    assert error.expected_kind == expected_kind  # type: ignore[attr-defined]
    assert error.rejected_value == rejected_value  # type: ignore[attr-defined]
    assert error.required_form == required_form  # type: ignore[attr-defined]


@pytest.mark.parametrize("construct", PACKAGE_ENTRYPOINTS)
def test_package_entrypoints_bind_equal_context_and_relationships(construct):
    package = construct(VALID_CHILD_PARENT_PACKAGE)
    child = package.resources[1]
    assert child._package_resource_names is package.resources[0]._package_resource_names
    assert child._validated_foreign_keys()[0].reference.resource == "parent"


@pytest.mark.parametrize("construct", PACKAGE_ENTRYPOINTS)
@pytest.mark.parametrize(
    ("raw", "error_type", "path", "resource_name", "rejected", "required_form"),
    [
        (
            {"resources": []},
            InvalidDescriptorStructure,
            "$.resources",
            None,
            [],
            "non-empty resource sequence",
        ),
        (
            {"resources": "resources.json"},
            InvalidDescriptorStructure,
            "$.resources",
            None,
            "resources.json",
            "resource sequence",
        ),
        (
            {"resources": [1]},
            InvalidDescriptorStructure,
            "$.resources[0]",
            None,
            1,
            "resource mapping",
        ),
        (
            {
                "resources": [
                    {"name": "orders", "path": "orders.csv"},
                    {"name": "orders", "path": "other.csv"},
                ]
            },
            InvalidDescriptorStructure,
            "$.resources[1].name",
            "orders",
            "orders",
            "unique resource name",
        ),
        (
            {
                "resources": [
                    {
                        "name": "orders",
                        "data": [],
                        "schema": {
                            "fields": [{"name": "id", "type": "integer"}],
                            "foreignKeys": [{"fields": [], "reference": {"fields": ["id"]}}],
                        },
                    }
                ]
            },
            InvalidDescriptorStructure,
            "$.resources[0].schema.foreignKeys[0].fields",
            "orders",
            [],
            "field name string or non-empty field name list",
        ),
        (
            {
                "resources": [
                    {
                        "name": "orders",
                        "data": [],
                        "schema": {
                            "fields": [{"name": "id", "type": "integer"}],
                            "foreignKeys": [
                                {
                                    "fields": ["id"],
                                    "reference": {"resource": "missing", "fields": ["id"]},
                                }
                            ],
                        },
                    }
                ]
            },
            InvalidDescriptorRelationship,
            "$.resources[0].schema.foreignKeys[0].reference.resource",
            "orders",
            "missing",
            "empty self-reference or package resource name",
        ),
    ],
)
def test_package_entrypoints_share_exact_error_fields(
    construct: Callable[[dict[str, object]], DataPackage],
    raw: dict[str, object],
    error_type: type[Exception],
    path: str,
    resource_name: str | None,
    rejected: object,
    required_form: str,
) -> None:
    with pytest.raises(error_type) as caught:
        construct(deepcopy(raw))
    _assert_error_fields(
        caught,
        error_type=error_type,
        descriptor_kind="package" if path == "$.resources" else "schema" if ".schema." in path else "resource",
        descriptor_path=path,
        resource_name=resource_name,
        reference=None,
        normalized_reference=None,
        expected_kind=None,
        rejected_value=rejected,
        required_form=required_form,
    )


def test_from_path_uses_the_same_package_error_fields(tmp_path: Path) -> None:
    raw = {"resources": [{"name": "orders", "path": "orders.csv", "type": "file"}]}
    descriptor_path = tmp_path / "datapackage.json"
    descriptor_path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(InvalidDescriptorStructure) as caught:
        DataPackage.from_path(descriptor_path)
    _assert_error_fields(
        caught,
        error_type=InvalidDescriptorStructure,
        descriptor_kind="resource",
        descriptor_path="$.resources[0].type",
        resource_name="orders",
        reference=None,
        normalized_reference=None,
        expected_kind=None,
        rejected_value="file",
        required_form="absent or 'table'",
    )


def test_json_and_python_root_errors_use_section_13_fields() -> None:
    for construct, rejected in (
        (lambda: DataPackage.model_validate_json("[]"), []),
        (lambda: DataPackage.from_json("[]"), []),
    ):
        with pytest.raises(InvalidDescriptorStructure) as caught:
            construct()
        _assert_error_fields(
            caught,
            error_type=InvalidDescriptorStructure,
            descriptor_kind="package",
            descriptor_path="$",
            resource_name=None,
            reference=None,
            normalized_reference=None,
            expected_kind=None,
            rejected_value=rejected,
            required_form="package descriptor mapping",
        )

    with pytest.raises(InvalidDescriptorStructure) as caught:
        DataPackage.model_validate([])
    _assert_error_fields(
        caught,
        error_type=InvalidDescriptorStructure,
        descriptor_kind="package",
        descriptor_path="$",
        resource_name=None,
        reference=None,
        normalized_reference=None,
        expected_kind=None,
        rejected_value=[],
        required_form="mapping or DataPackage instance",
    )


def test_json_text_entrypoints_share_syntax_error_fields() -> None:
    for construct in (
        lambda: DataPackage.model_validate_json("{"),
        lambda: DataPackage.from_json("{"),
    ):
        with pytest.raises(InvalidDescriptorSyntax) as caught:
            construct()
        _assert_error_fields(
            caught,
            error_type=InvalidDescriptorSyntax,
            descriptor_kind="package",
            descriptor_path="$",
            resource_name=None,
            reference=None,
            normalized_reference=None,
            expected_kind=None,
            rejected_value="{",
            required_form="valid JSON text",
        )


def test_relationship_construction_matrix_has_constraint_edge_without_dependency_edge(
    tmp_path: Path,
) -> None:
    schema = {
        "fields": [
            {"name": "id", "type": "integer"},
            {"name": "parent_id", "type": "integer"},
        ],
        "foreignKeys": [
            {
                "fields": ["parent_id"],
                "reference": {"resource": "parent", "fields": ["id"]},
            }
        ],
    }
    schema_path = tmp_path / "child-schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    raw = {
        "resources": [
            {"name": "parent", "path": "parent.csv", "type": "table", "schema": {"fields": [{"name": "id", "type": "integer"}]}},
            {"name": "child", "path": "child.csv", "type": "table", "schema": schema},
        ]
    }
    authored = TypeSpec(
        fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
            FieldSpec(name="parent_id", type=UniversalType.INTEGER),
        ],
        foreign_keys=[
            ForeignKey(
                fields=["parent_id"],
                reference=ForeignKeyReference(resource="parent", fields=["id"]),
            )
        ],
    )
    packages = (
        DataPackage.from_descriptor(raw),
        DataPackage.from_descriptor(
            {
                "resources": [
                    raw["resources"][0],
                    {"name": "child", "path": "child.csv", "type": "table", "schema": schema_path.name},
                ]
            },
            base_uri=tmp_path,
        ),
        DataPackage(resources=[DataResource(**raw["resources"][0]), DataResource(**raw["resources"][1])]),
        DataPackage(
            resources=[
                DataResource(**raw["resources"][0]),
                DataResource(name="child", path="child.csv", type="table", table_schema=schema_path.as_uri()),
            ]
        ),
        DataPackage(
            resources=[
                DataResource(**raw["resources"][0]),
                DataResource(name="child", path="child.csv", type="table", table_schema=authored),
            ]
        ),
    )

    for package in packages:
        child = package.resources[1]
        assert child.to_typespec() is not None
        dag = package.to_relation_dag()
        assert dag.constraint_edges == {("parent", "child")}
        assert dag.dependency_edges == set()
        assert len(dag.constraint_metadata[("parent", "child")]) == 1


def test_referenced_schema_errors_keep_exact_reference_fields(tmp_path: Path) -> None:
    missing = tmp_path / "missing-schema.json"
    package = DataPackage(
        resources=[DataResource(name="child", path="child.csv", type="table", table_schema=missing.as_uri())]
    )
    with pytest.raises(DescriptorReferenceNotFound) as caught:
        package.resources[0].to_typespec()
    _assert_error_fields(
        caught,
        error_type=DescriptorReferenceNotFound,
        descriptor_kind="schema",
        descriptor_path="$.resources[0].schema",
        resource_name="child",
        reference=missing.as_uri(),
        normalized_reference=missing.as_uri(),
        expected_kind="schema",
        rejected_value=missing.as_uri(),
        required_form="existing descriptor document",
    )

    relative = DataPackage(
        resources=[DataResource(name="child", path="child.csv", type="table", table_schema="schema.json")]
    )
    with pytest.raises(MissingDescriptorBase) as relative_caught:
        relative.resources[0].to_typespec()
    _assert_error_fields(
        relative_caught,
        error_type=MissingDescriptorBase,
        descriptor_kind="schema",
        descriptor_path="$.resources[0].schema",
        resource_name="child",
        reference="schema.json",
        normalized_reference=None,
        expected_kind=None,
        rejected_value="schema.json",
        required_form="absolute URI or relative reference with base URI",
    )

    denied_reference = "https://example.com/schema.json"
    denied = DataPackage(
        resources=[
            DataResource(
                name="child",
                path="child.csv",
                type="table",
                table_schema=denied_reference,
            )
        ]
    )
    with pytest.raises(DescriptorReferenceSchemeDenied) as denied_caught:
        denied.resources[0].to_typespec()
    _assert_error_fields(
        denied_caught,
        error_type=DescriptorReferenceSchemeDenied,
        descriptor_kind="schema",
        descriptor_path="$.resources[0].schema",
        resource_name="child",
        reference=denied_reference,
        normalized_reference=denied_reference,
        expected_kind="schema",
        rejected_value=denied_reference,
        required_form="approved descriptor reference scheme",
    )



def test_context_ownership_and_preserve_serialization_are_entrypoint_invariants(tmp_path: Path) -> None:
    for construct in PACKAGE_ENTRYPOINTS:
        input_raw = deepcopy(VALID_CHILD_PARENT_PACKAGE)
        package = construct(input_raw)
        expected_sources = deepcopy(input_raw["sources"])
        input_raw["sources"][0]["meta"]["owners"].append("mutated")
        assert package.resources[0].effective_sources == expected_sources
        assert package.resources[0].effective_sources is not package.resources[0].effective_sources
        assert package.to_descriptor() == VALID_CHILD_PARENT_PACKAGE

    descriptor_path = tmp_path / "datapackage.json"
    descriptor_path.write_text(json.dumps(VALID_CHILD_PARENT_PACKAGE), encoding="utf-8")
    package = DataPackage.from_path(descriptor_path)
    assert package.to_descriptor() == VALID_CHILD_PARENT_PACKAGE


def test_collect_uses_package_context_and_returns_fixture_rows() -> None:
    package = DataPackage(**VALID_CHILD_PARENT_PACKAGE)
    dag = package.to_relation_dag()
    result = dag.collect("child").collect()
    assert result.rows(named=True) == [{"id": 10, "parent_id": 1}]
    assert isinstance(result, pl.DataFrame)
