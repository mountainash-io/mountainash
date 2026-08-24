import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.relations.schema_inference import SchemaTypeStatus, infer_schema


def test_dataframe_schema_is_canonical():
    r = ma.relation(pl.DataFrame({"a": [1], "b": ["x"]}))
    schema = infer_schema(r._node)
    assert schema == {"a": D.I64, "b": D.STRING}


def test_uninferable_measure_is_unknown_status():
    r = ma.relation(pl.DataFrame({"a": [1]})).group_by("a").agg(
        ma.col("a").sum().alias("total")
    )
    schema = infer_schema(r._node)
    assert schema["total"] is SchemaTypeStatus.UNKNOWN


def test_python_source_data_infers_types():
    # Oracle: pl.DataFrame([{"x": 1}], strict=False).schema -> {"x": Int64}
    # -> registry.from_native(Int64, target=POLARS) -> D.I64
    dag = ma.RelationDAG()
    # dag.source(name, data) registers a SourceRelNode-backed relation under
    # ``name`` and returns a *ref* to it; pull the source relation itself so we
    # infer the SourceRelNode schema (intent: a python-source-backed relation).
    dag.source("raw", [{"x": 1}])
    source_rel = dag.relations["raw"]
    schema = infer_schema(source_rel._node)
    assert schema["x"] == D.I64  # oracle: pl.DataFrame([{"x":1}], strict=False) -> Int64


def test_any_resource_field_is_unconstrained():
    from mountainash.relations.schema_inference import _schema_from_table_schema
    schema = _schema_from_table_schema(
        {"fields": [{"name": "a", "type": "any"}, {"name": "n", "type": "integer"}]}
    )
    assert schema["a"] is SchemaTypeStatus.UNCONSTRAINED
    assert schema["n"] is D.I64


@pytest.mark.parametrize(
    ("type_name", "format_name", "expected"),
    [
        ("geopoint", "default", D.STRING),
        ("geopoint", "array", D.LIST),
        ("geopoint", "object", D.STRUCT),
        ("geojson", "default", D.JSON),
        ("geojson", "topojson", D.JSON),
    ],
)
def test_resource_read_schema_uses_field_aware_geospatial_canonical(
    type_name, format_name, expected
):
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    from mountainash.typespec.datapackage import DataResource
    resource = DataResource(
        name="geo",
        data=[],
        table_schema={"fields": [{"name": "shape", "type": type_name, "format": format_name}]},
    )
    assert infer_schema(ResourceReadRelNode(resource=resource)) == {"shape": expected}


@pytest.mark.parametrize(
    "field",
    [
        {"name": "shape", "type": "geopoint", "format": "invalid"},
        {"name": "shape", "type": "geojson", "format": "invalid"},
        {"name": "shape", "type": "not-a-type"},
        {"name": "shape"},
    ],
)
def test_resource_read_schema_unknown_for_malformed_or_absent_schema_evidence(field):
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    from mountainash.typespec.datapackage import DataResource

    resource = DataResource(name="geo", data=[], table_schema={"fields": [field]})
    assert infer_schema(ResourceReadRelNode(resource=resource)) == {
        "shape": SchemaTypeStatus.UNKNOWN
    }
