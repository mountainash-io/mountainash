import polars as pl

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


def test_python_source_data_is_unknown_status():
    dag = ma.RelationDAG()
    # dag.source(name, data) registers a SourceRelNode-backed relation under
    # ``name`` and returns a *ref* to it; pull the source relation itself so we
    # infer the SourceRelNode schema (intent: a python-source-backed relation).
    dag.source("raw", [{"x": 1}])
    source_rel = dag.relations["raw"]
    schema = infer_schema(source_rel._node)
    assert schema["x"] is SchemaTypeStatus.UNKNOWN


def test_any_resource_field_is_unconstrained():
    from mountainash.relations.schema_inference import _schema_from_table_schema
    schema = _schema_from_table_schema(
        {"fields": [{"name": "a", "type": "any"}, {"name": "n", "type": "integer"}]}
    )
    assert schema["a"] is SchemaTypeStatus.UNCONSTRAINED
    assert schema["n"] is D.I64
