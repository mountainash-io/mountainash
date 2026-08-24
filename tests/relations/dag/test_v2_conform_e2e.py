"""Public Frictionless v2 descriptor -> DAG -> conform -> collection proof."""
from __future__ import annotations

import narwhals as nw
import polars as pl
import pytest
import mountainash as ma
from mountainash.core.capabilities import CapabilityRegistry
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
)
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem
from mountainash.expressions.core.unified_visitor.visitor import UnifiedExpressionVisitor
from mountainash.typespec.datapackage import DataPackage


def _descriptor() -> dict:
    return {
        "$schema": "https://datapackage.org/profiles/2.0/datapackage.json",
        "name": "unit-c-public-smoke",
        "resources": [
            {
                "type": "table",
                "name": "records",
                "data": [],
                "schema": {
                    "$schema": "https://datapackage.org/profiles/2.0/tableschema.json",
                    "missingValues": [{"value": "NA"}],
                    "fields": [
                        {"name": "tags", "type": "list", "itemType": "integer", "delimiter": "|"},
                        {
                            "name": "items",
                            "type": "array",
                            "x-mountainash": {
                                "item_object_fields": [
                                    {"name": "code", "type": "integer"},
                                    {
                                        "name": "payload",
                                        "type": "object",
                                        "x-mountainash": {
                                            "object_fields": [{"name": "score", "type": "integer"}]
                                        },
                                    },
                                ]
                            },
                        },
                        {
                            "name": "payload",
                            "type": "object",
                            "x-mountainash": {
                                "object_fields": [
                                    {"name": "id", "type": "integer"},
                                    {"name": "label", "type": "string"},
                                ]
                            },
                        },
                        {"name": "point_default", "type": "geopoint", "format": "default"},
                        {"name": "point_array", "type": "geopoint", "format": "array"},
                        {"name": "topology", "type": "geojson", "format": "topojson"},
                        {"name": "point_object", "type": "geopoint", "format": "object"},
                        {"name": "geometry", "type": "geojson", "format": "default"},
                        {"name": "when", "type": "datetime"},
                        {"name": "duration", "type": "duration"},
                        {"name": "year", "type": "year"},
                        {"name": "yearmonth", "type": "yearmonth"},
                        {"name": "any_time", "type": "datetime", "format": "any"},
                    ],
                },
            }
        ],
    }


def _native_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "tags": ["1|2", "NA", None],
            "items": [
                [{"code": "7", "payload": {"score": "3"}}],
                None,
                [],
            ],
            "payload": [{"id": "9", "label": "first"}, None, {"id": "10", "label": "third"}],
            "point_default": ["1.0, 2.0", None, "3.0, 4.0"],
            "point_array": [[1.0, 2.0], None, [3.0, 4.0]],
            "topology": [{"type": "Topology", "objects": {}}, None, {"type": "Topology", "objects": {}}],
            "point_object": [{"lon": 1.0, "lat": 2.0}, None, {"lon": 3.0, "lat": 4.0}],
            "geometry": ['{"type":"Point","coordinates":[1,2]}', None, '{"type":"Point","coordinates":[3,4]}'],
            "when": ["2024-01-02T03:04:05", None, "2024-02-03T04:05:06"],
            "duration": ["P1DT2H", None, "PT30M"],
            "year": ["2024", None, "2025"],
            "yearmonth": ["2024-01", None, "2025-02"],
            "any_time": ["2024-01-02T03:04:05", None, "2024-02-03T04:05:06"],
        }
    )


def test_public_descriptor_dag_conform_collect() -> None:
    package = DataPackage.from_descriptor(_descriptor())
    dag = package.to_relation_dag(overrides={"records": _native_frame()})
    assert package.resources[0].name == "records"
    result = dag.collect("records")
    if isinstance(result, pl.LazyFrame):
        result = result.collect()

    assert result.columns == [
        "tags", "items", "payload", "point_default", "point_array", "topology",
        "point_object", "geometry", "when", "duration", "year", "yearmonth", "any_time",
    ]
    assert result["tags"].to_list() == [[1, 2], None, None]
    assert result["items"].to_list() == [[{"code": 7, "payload": {"score": 3}}], None, []]
    assert result["payload"].to_list() == [{"id": 9, "label": "first"}, None, {"id": 10, "label": "third"}]
    assert result["point_default"].to_list() == ["1.0, 2.0", None, "3.0, 4.0"]
    assert result["point_array"].to_list() == [[1.0, 2.0], None, [3.0, 4.0]]
    assert result["point_object"].to_list() == [{"lon": 1.0, "lat": 2.0}, None, {"lon": 3.0, "lat": 4.0}]
    assert result["geometry"].to_list()[0] == '{"type":"Point","coordinates":[1,2]}'
    assert result["topology"].to_list()[0] == '{"type":"Topology","objects":{}}'
    native_geojson = ma.col("native").geo.serialize_geojson(format="default", field_name="native")
    native_compiled = UnifiedExpressionVisitor(PolarsExpressionSystem("polars")).visit(
        native_geojson._node
    )
    native_result = pl.DataFrame(
        {"native": [{"type": "Point", "coordinates": [1.0, 2.0]}]}
    ).select(native_compiled)
    assert native_result["native"].to_list() == ['{"type":"Point","coordinates":[1.0,2.0]}']
    assert result["when"].to_list()[0].year == 2024
    assert result["duration"].to_list()[0] is not None
    assert result["year"].to_list() == ["2024", None, "2025"]
    assert result["any_time"].to_list()[0].year == 2024
    assert not any("marker" in name.lower() for name in result.columns)

def test_public_conform_reports_exact_declared_capability_error() -> None:
    descriptor = {
        "name": "unit-c-capability-smoke",
        "resources": [
            {
                "name": "records",
                "type": "table",
                "data": [],
                "schema": {
                    "fields": [
                        {"name": "point", "type": "geopoint", "format": "array"},
                    ]
                },
            }
        ],
    }
    package = DataPackage.from_descriptor(descriptor)
    dag = package.to_relation_dag(
        overrides={"records": nw.from_native(pl.DataFrame({"point": ["[1,2]"]}))}
    )
    matching_facts = [
        candidate
        for candidate in CapabilityRegistry.facts(
            backend=CONST_BACKEND.NARWHALS
        )
        if candidate.operation_key is FK_GEO.PARSE_GEOPOINT
        and candidate.param == "format"
        and candidate.predicate is not None
        and {(clause.path, clause.operand) for clause in candidate.predicate.clauses}
        == {("format", "array"), ("source_representation", "lexical")}
    ]
    assert len(matching_facts) == 1
    fact = matching_facts[0]
    with pytest.raises(BackendCapabilityError) as exc_info:
        dag.collect("records", backend="narwhals")
    error = exc_info.value
    assert error.backend == "narwhals"
    assert error.function_key is FK_GEO.PARSE_GEOPOINT
    assert error.limitation is fact
