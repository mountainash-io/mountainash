import json
from pathlib import Path

import pytest

from fixtures.backend_registry import ALL_BACKENDS

from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec import LabeledValue, UniversalType, resolve_field_canonical
from mountainash.typespec.datapackage import DataPackage
from mountainash.typespec.errors import InvalidDescriptorStructure
from mountainash.typespec.frictionless import (
    migrate_nested_field_declarations,
    table_schema_to_frictionless,
)


def test_v2_descriptor_path_smoke(tmp_path: Path) -> None:
    schema = {
        "$schema": "https://datapackage.org/profiles/2.0/tableschema.json",
        "fields": [{"name": "id", "type": "integer"}],
    }
    dialect = {
        "$schema": "https://datapackage.org/profiles/2.0/tabledialect.json",
        "delimiter": ";",
    }
    descriptor = {
        "name": "smoke",
        "sources": [{"title": "catalog"}],
        "resources": [{
            "name": "orders",
            "path": "orders.csv",
            "type": "table",
            "schema": "schema.json",
            "dialect": "dialect.json",
        }],
    }
    (tmp_path / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
    (tmp_path / "dialect.json").write_text(json.dumps(dialect), encoding="utf-8")
    (tmp_path / "orders.csv").write_text("id\n1\n", encoding="utf-8")
    path = tmp_path / "datapackage.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")

    package = DataPackage.from_path(path)
    resource = package.resources[0]
    assert package._descriptor_context.base_uri == tmp_path.resolve().as_uri() + "/"
    assert resource.table_schema == "schema.json"
    assert resource.to_table_schema().field_names == ["id"]
    assert resource.dialect == "dialect.json"
    assert resource.to_dialect().delimiter == ";"
    assert resource.effective_sources == [{"title": "catalog"}]

    preserve = package.to_descriptor()
    canonical = package.to_canonical_descriptor()
    preserve["resources"][0]["schema"] = "changed"
    canonical["sources"][0]["title"] = "changed"
    assert package.to_descriptor() == descriptor
    assert package.to_canonical_descriptor()["resources"][0]["schema"] == "schema.json"


def test_v2_table_schema_cutover_smoke() -> None:
    descriptor = {
        "$schema": "https://datapackage.org/profiles/2.0/datapackage.json",
        "name": "typed-v2",
        "resources": [
            {
                "$schema": "https://datapackage.org/profiles/2.0/dataresource.json",
                "name": "records",
                "data": [],
                "schema": {
                    "$schema": "https://datapackage.org/profiles/2.0/tableschema.json",
                    "missingValues": [{"value": "NA", "label": "Not available"}],
                    "foreignKeys": [
                        {
                            "fields": "parent_id",
                            "reference": {"fields": "id"},
                        }
                    ],
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {"name": "parent_id", "type": "integer"},
                        {"name": "untyped"},
                        {"name": "tags", "type": "list", "itemType": "string", "delimiter": ";"},
                        {
                            "name": "items",
                            "type": "array",
                            "x-mountainash": {
                                "element": {
                                    "type": "object",
                                    "x-mountainash": {"fields": [{"name": "code", "type": "string"}]},
                                }
                            },
                        },
                        {"name": "point", "type": "geopoint", "format": "array"},
                        {"name": "geometry", "type": "geojson"},
                        {
                            "name": "score",
                            "type": "integer",
                            "categories": [{"value": 1, "label": "One"}],
                            "missingValues": [{"value": "-", "label": "Dash"}],
                            "constraints": {
                                "exclusiveMinimum": 0,
                                "exclusiveMaximum": 10,
                                "jsonSchema": {"type": "integer"},
                            },
                        },
                        {"name": "when", "type": "datetime", "format": "fmt:%Y-%m-%d"},
                        {"name": "duration", "type": "duration"},
                        {"name": "year", "type": "year"},
                        {"name": "yearmonth", "type": "yearmonth"},
                    ],
                },
            }
        ],
    }

    package = DataPackage.from_descriptor(descriptor)
    raw_schema = package.resources[0].table_schema
    spec = package.resources[0].to_table_schema()

    assert raw_schema == descriptor["resources"][0]["schema"]
    assert spec is not None
    assert spec.fields_match == "exact"
    assert spec.get_field("untyped").type is UniversalType.ANY
    assert spec.get_field("tags").type is UniversalType.LIST
    assert list(spec.get_field("items").element.fields) == ["code"]
    assert spec.get_field("items").element.fields["code"].type is UniversalType.STRING
    assert resolve_field_canonical(spec.get_field("point")) is MountainashDtype.LIST
    assert resolve_field_canonical(spec.get_field("geometry")) is MountainashDtype.JSON
    assert spec.foreign_keys[0].fields == ["parent_id"]
    assert spec.foreign_keys[0].reference.resource is None
    assert spec.get_field("when").format == "%Y-%m-%d"

    assert spec.missing_values == [LabeledValue("NA", "Not available")]

    tags = spec.get_field("tags")
    assert tags is not None
    assert tags.item_type == "string"
    assert tags.delimiter == ";"

    score = spec.get_field("score")
    assert score is not None
    assert list(score.categories) == [LabeledValue(1, "One")]
    assert list(score.missing_values) == [LabeledValue("-", "Dash")]
    assert score.constraints is not None
    assert score.constraints.exclusive_minimum == 0
    assert score.constraints.exclusive_maximum == 10
    assert score.constraints.json_schema == {"type": "integer"}

    assert resolve_field_canonical(
        spec.get_field("duration")
    ) is MountainashDtype.XSD_DURATION
    assert resolve_field_canonical(
        spec.get_field("year")
    ) is MountainashDtype.XSD_YEAR
    assert resolve_field_canonical(
        spec.get_field("yearmonth")
    ) is MountainashDtype.XSD_YEARMONTH

    typed_descriptor = table_schema_to_frictionless(spec)
    assert "type" not in next(f for f in typed_descriptor["fields"] if f["name"] == "untyped")
    assert typed_descriptor["foreignKeys"][0]["reference"] == {"fields": ["id"]}
    assert typed_descriptor["missingValues"] == [
        {"value": "NA", "label": "Not available"}
    ]
    typed_tags = next(
        field for field in typed_descriptor["fields"] if field["name"] == "tags"
    )
    assert typed_tags["itemType"] == "string"
    assert typed_tags["delimiter"] == ";"
    typed_score = next(
        field for field in typed_descriptor["fields"] if field["name"] == "score"
    )
    assert typed_score["categories"] == [{"value": 1, "label": "One"}]
    assert typed_score["missingValues"] == [{"value": "-", "label": "Dash"}]
    assert typed_score["constraints"] == {
        "exclusiveMinimum": 0,
        "exclusiveMaximum": 10,
        "jsonSchema": {"type": "integer"},
    }


def test_legacy_nested_descriptor_is_preserved_raw_and_needs_explicit_migration() -> None:
    legacy_schema = {
        "fields": [{
            "name": "items",
            "type": "array",
            "x-mountainash": {"item_object_fields": [{"name": "code", "type": "string"}]},
        }],
    }
    descriptor = {"name": "legacy", "resources": [
        {"name": "records", "data": [], "schema": legacy_schema},
    ]}
    package = DataPackage.from_descriptor(descriptor)
    resource = package.resources[0]

    assert package.to_descriptor() == descriptor
    assert resource.table_schema == legacy_schema
    with pytest.raises(InvalidDescriptorStructure, match="migrate_nested_field_declarations"):
        resource.to_table_schema()
    assert package.to_descriptor() == descriptor

    migrated = migrate_nested_field_declarations(resource.table_schema)
    assert migrated is not resource.table_schema
    element = DataPackage.from_descriptor(
        {"name": "migrated", "resources": [{"name": "records", "data": [], "schema": migrated}]}
    ).resources[0].to_table_schema().fields["items"].element
    assert list(element.fields) == ["code"]
    assert element.fields["code"].type is UniversalType.STRING


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_migrated_legacy_descriptor_conforms_and_validates(backend_name, backend_factory):
    """Old mixed descriptor -> explicit migration -> JSON text -> typed -> conform -> validation."""
    from copy import deepcopy

    import polars as pl
    from ibis.common.exceptions import UnsupportedBackendType

    import mountainash as ma
    from fixtures.call_expectations import expect_call_failure
    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec.frictionless import table_schema_from_frictionless
    from mountainash.validation import ValidationRunner

    legacy = {"fields": [{"name": "record", "type": "object", "x-mountainash": {
        "dtype": {"kind": "struct", "fields": [
            {"name": "quantity", "dtype": {"kind": "canonical", "name": "i64"}},
        ]},
        "object_fields": [{
            "name": "quantity", "type": "string", "constraints": {"minimum": 0},
            "x-mountainash": {"null_fill": 7},
        }],
    }}]}
    original = deepcopy(legacy)
    schema = table_schema_from_frictionless(json.loads(json.dumps(migrate_nested_field_declarations(legacy))))
    assert legacy == original
    with expect_call_failure(
        when=backend_name == "ibis-sqlite",
        errors=(UnsupportedBackendType,),
        reason="SQLite cannot construct the native Struct input",
    ):
        source = backend_factory.create(
            {"record": [{"quantity": "2"}, {"quantity": None}, {"quantity": "-3"}]}, backend_name,
        )
    conformed = ma.relation(source).conform(schema)
    assert conformed.to_polars()["record"].to_list() == [{"quantity": 2}, {"quantity": 7}, {"quantity": -3}]
    result = ValidationRunner().validate_relation(conformed, plan=compile_datacontract(schema))
    nested = result.check_summaries.filter(pl.col("check_id") == "record_nested").row(0, named=True)
    assert (nested["status"], nested["pass_count"], nested["fail_count"]) == ("failed", 2, 1), backend_name
