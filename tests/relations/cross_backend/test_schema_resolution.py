"""Public schema inspection describes actual outputs without collecting rows."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D, dtype_family
from fixtures.backend_registry import ALL_BACKENDS, REGISTRY

SCHEMA_BACKENDS = [*ALL_BACKENDS, "pyarrow", "narwhals-pyarrow"]


def _source(backend_name, data, name):
    if backend_name in {"pandas", "narwhals-pandas"} and isinstance(data, pl.DataFrame):
        import narwhals as nw

        frame = data.to_pandas()
        return nw.from_native(frame) if backend_name == "narwhals-pandas" else frame
    if backend_name in {"pyarrow", "narwhals-pyarrow"}:
        import narwhals as nw
        import pyarrow as pa

        table = data.to_arrow() if isinstance(data, pl.DataFrame) else pa.table(data)
        return nw.from_native(table) if backend_name == "narwhals-pyarrow" else table
    return REGISTRY[backend_name].build(data, name)


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_computed_schema_is_complete_and_replaces_input_names(backend_name):
    source = _source(backend_name, {"n": [2, 7]}, "schema_computed")
    relation = ma.relation(source).select(ma.col("n").add(1).alias("next"))
    schema = relation.schema
    assert list(schema) == ["next"]
    assert dtype_family(schema["next"]) == D.I64
    assert relation.collect_schema() == schema
    assert relation.collect_schema(allow_execution=True) == schema
    assert relation.to_dict() == {"next": [3, 8]}


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_returned_schema_is_independent_of_subsequent_inspection(backend_name):
    source = _source(backend_name, {"n": [2, 7]}, "schema_independent")
    relation = ma.relation(source).select(ma.col("n").add(1).alias("next"))
    first = relation.collect_schema()
    first.clear()
    actual = relation.schema
    assert list(actual) == ["next"]
    assert dtype_family(actual["next"]) == D.I64


@pytest.mark.parametrize("backend_name", [name for name in SCHEMA_BACKENDS if name != "ibis-sqlite"])
@pytest.mark.parametrize("timezone", [None, "Europe/London"])
def test_union_schema_describes_widened_timestamp_output(backend_name, timezone):
    # SQLite physical temporal storage is qualified in the SQL owner suite.
    left = pl.DataFrame({"at": pl.Series([1], dtype=pl.Datetime("ms", timezone))})
    right = pl.DataFrame({"at": pl.Series([2], dtype=pl.Datetime("ns", timezone))})
    source_left = _source(backend_name, left, "schema_union_left")
    if backend_name.startswith("ibis-"):
        source_right = source_left._find_backend().create_table("schema_union_right", right)
    else:
        source_right = _source(backend_name, right, "schema_union_right")
    relation = ma.concat([ma.relation(source_left), ma.relation(source_right)])
    schema = relation.schema
    sql_aware = bool(timezone) and backend_name == "ibis-duckdb"
    assert schema["at"].precision == (6 if sql_aware else 9)
    assert schema["at"].timezone_aware is (timezone is not None)
    assert schema["at"].timezone == (None if backend_name == "ibis-duckdb" else timezone)
    assert relation.collect_schema() == schema
    assert relation.collect_schema(allow_execution=True) == schema
    actual = relation.to_polars()
    output_zone = "UTC" if timezone and backend_name == "ibis-duckdb" else timezone
    assert actual.schema["at"] == pl.Datetime("us" if sql_aware else "ns", output_zone)
    assert actual["at"].cast(pl.Int64).to_list() == (
        [1_000, 0] if sql_aware else [1_000_000, 2]
    )


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_dag_named_and_fluent_schema_use_output_types(backend_name):
    source = _source(backend_name, {"n": [2, 7]}, "schema_dag")
    dag = ma.RelationDAG()
    dag.add("base", ma.relation(source))
    output = dag.ref("base").select(ma.col("n").add(1).alias("next"))
    dag.add("output", output)
    named = dag.schema("output")
    assert list(named) == ["next"]
    assert dtype_family(named["next"]) == D.I64
    assert output.schema == named
    assert output.collect_schema() == named
    assert output.collect_schema(allow_execution=True) == named
    assert output.to_dict() == {"next": [3, 8]}


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_metadata_does_not_enforce_conform_freeze_but_execution_does(backend_name):
    from mountainash.conform.errors import SchemaDriftError
    from mountainash.typespec.spec import FieldDefinition, TableSchema
    from mountainash.typespec.universal_types import UniversalType

    source = _source(backend_name, {"n": [2, 7], "extra": [3, 4]}, "schema_freeze")
    spec = TableSchema(fields={"n": FieldDefinition(type=UniversalType.INTEGER)}, fields_match="open")
    relation = ma.relation(source).conform(spec, contract={"extra_columns": "freeze"})
    schema = relation.collect_schema()
    # The frozen extra column has no successful execution to describe; only the
    # declared field's type and the execution-time refusal are contractual.
    assert dtype_family(schema["n"]) is D.I64
    with pytest.raises(SchemaDriftError):
        relation.to_dict()


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_join_schema_does_not_copy_types_before_nullable_promotion(backend_name):
    from mountainash.core.dtypes import SchemaTypeStatus
    from mountainash.exceptions import IncompleteSchemaError

    left = _source(backend_name, {"k": [1, 2]}, "schema_join_left")
    if backend_name.startswith("ibis-"):
        right = left._find_backend(use_default=False).create_table(
            "schema_join_right", pl.DataFrame({"k": [1], "value": [9]}).to_arrow(),
        )
    else:
        right = _source(backend_name, {"k": [1], "value": [9]}, "schema_join_right")
    relation = ma.relation(left).join(right, on="k", how="left")
    if backend_name in {"pandas", "narwhals-pandas"}:
        assert relation.schema["value"] is SchemaTypeStatus.UNKNOWN
        with pytest.raises(IncompleteSchemaError):
            relation.collect_schema()
        expected = D.FP64
    else:
        assert dtype_family(relation.collect_schema()["value"]) is D.I64
        expected = D.I64
    assert dtype_family(relation.collect_schema(allow_execution=True)["value"]) is expected
    result = relation.to_polars().sort("k")
    assert result.to_dict(as_series=False) == {"k": [1, 2], "value": [9, None]}
    assert result.schema["value"] == (pl.Float64 if expected is D.FP64 else pl.Int64)


@pytest.mark.parametrize("backend_name", ["pandas", "narwhals-pandas"])
def test_asof_schema_does_not_certify_empty_pandas_integer_payload(backend_name):
    """pandas promotes unmatched ASOF payloads just as in a left join."""
    from mountainash.core.dtypes import SchemaTypeStatus
    from mountainash.exceptions import IncompleteSchemaError

    left = _source(backend_name, {"k": [1, 2]}, "schema_asof_left")
    right = _source(backend_name, {"k": [2], "value": [9]}, "schema_asof_right")
    relation = ma.relation(left).join_asof(right, on="k", strategy="backward")
    assert relation.schema["value"] is SchemaTypeStatus.UNKNOWN
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()
    assert dtype_family(relation.collect_schema(allow_execution=True)["value"]) is D.FP64
    assert relation.to_polars().to_dict(as_series=False) == {"k": [1, 2], "value": [None, 9.0]}
