import json
from pathlib import Path

from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec import LabeledValue, UniversalType, resolve_field_canonical
from mountainash.typespec.datapackage import DataPackage
from mountainash.typespec.frictionless import typespec_to_frictionless


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
    assert resource.to_typespec().field_names == ["id"]
    assert resource.dialect == "dialect.json"
    assert resource.to_dialect().delimiter == ";"
    assert resource.effective_sources == [{"title": "catalog"}]

    preserve = package.to_descriptor()
    canonical = package.to_canonical_descriptor()
    preserve["resources"][0]["schema"] = "changed"
    canonical["sources"][0]["title"] = "changed"
    assert package.to_descriptor() == descriptor
    assert package.to_canonical_descriptor()["resources"][0]["schema"] == "schema.json"


def test_unit_b_typespec_cutover_smoke() -> None:
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
                                "item_object_fields": [{"name": "code", "type": "string"}]
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
    spec = package.resources[0].to_typespec()

    assert raw_schema == descriptor["resources"][0]["schema"]
    assert spec is not None
    assert spec.fields_match == "exact"
    assert spec.get_field("untyped").type is UniversalType.ANY
    assert spec.get_field("tags").type is UniversalType.LIST
    assert spec.get_field("items").item_object_fields[0].name == "code"
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
    assert score.categories == [LabeledValue(1, "One")]
    assert score.missing_values == [LabeledValue("-", "Dash")]
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

    typed_descriptor = typespec_to_frictionless(spec)
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

