"""Opt-in schema completion preserves execution, validation and ownership."""
from __future__ import annotations

import ibis
import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS, REGISTRY
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.exceptions import IncompleteSchemaError


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_pivot_completion_preserves_supported_native_behavior(backend_name):
    source = REGISTRY[backend_name].build(
        {"id": [1, 1], "category": ["a", "b"], "amount": [10, 20]}, "schema_pivot",
    )
    relation = ma.relation(source).pivot(on="category", index="id", values="amount")
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()
    error = TypeError if backend_name.startswith("ibis-") else (
        AttributeError if backend_name == "narwhals-lazy" else None
    )
    if error is not None:
        # These routes already reject ordinary pivot execution; permission must
        # preserve that failure rather than invent an empty output schema.
        with pytest.raises(error):
            relation.to_dict()
        with pytest.raises(error):
            relation.collect_schema(allow_execution=True)
    else:
        assert relation.collect_schema(allow_execution=True) == {
            "id": D.I64, "a": D.I64, "b": D.I64,
        }
        assert relation.to_dict() == {"id": [1], "a": [10], "b": [20]}


@pytest.mark.parametrize("value", ["17", "bad"])
def test_sql_fallback_evaluates_output_and_releases_owned_tables(value):
    """A transferred input does not mean the deferred SQL output was evaluated."""
    import duckdb

    left_connection = ibis.duckdb.connect()
    right_connection = ibis.duckdb.connect()
    try:
        left = left_connection.create_table("schema_left", {"id": [1]})
        right = right_connection.create_table("schema_right", {"id": [1], "value": [value]})
        relation = ma.relation(left).join(right, on="id").select(ma.col("value").cast("int64"))
        before = set(left_connection.list_tables())
        with pytest.raises(IncompleteSchemaError):
            relation.collect_schema()
        assert set(left_connection.list_tables()) == before
        if value == "bad":
            with pytest.raises(duckdb.ConversionException):
                relation.collect_schema(allow_execution=True)
        else:
            assert relation.collect_schema(allow_execution=True) == {"value": D.I64}
        assert set(left_connection.list_tables()) == before
        if value == "17":
            assert relation.to_dict() == {"value": [17]}
        assert right.execute()["value"].tolist() == [value]
    finally:
        right_connection.disconnect()
        left_connection.disconnect()


@pytest.mark.parametrize("year", ["2024", "bad"])
def test_schema_fallback_preserves_source_residue_and_cleanup(checked_year, year):
    from mountainash.core.types import BackendCapabilityError

    source = REGISTRY["ibis-duckdb"].build({"id": [1], "year": [year]}, "schema_year")
    other = REGISTRY["ibis-duckdb"].build({"id": [1]}, "schema_other")
    connection = source._find_backend(use_default=False)
    other_connection = other._find_backend(use_default=False)
    try:
        relation = ma.relation(source).conform(checked_year).join(other, on="id").select("id")
        before = set(connection.list_tables())
        with pytest.raises(IncompleteSchemaError):
            relation.collect_schema()
        if year == "bad":
            with pytest.raises(BackendCapabilityError, match="year residue"):
                relation.collect_schema(allow_execution=True)
        else:
            assert relation.collect_schema(allow_execution=True) == {"id": D.I64}
        assert set(connection.list_tables()) == before
        assert source.execute()["year"].tolist() == [year]
    finally:
        other_connection.disconnect()
        connection.disconnect()


def test_value_dependent_completion_does_not_retain_previous_rows():
    import pandas as pd

    source = pd.DataFrame({"id": [1], "category": ["a"], "amount": [10]})
    relation = ma.relation(source).pivot(on="category", index="id", values="amount")
    assert relation.collect_schema(allow_execution=True) == {"id": D.I64, "a": D.I64}
    source.loc[1] = [1, "b", 20]
    assert relation.collect_schema(allow_execution=True) == {"id": D.I64, "a": D.I64, "b": D.I64}
    assert relation.to_dict() == {"id": [1], "a": [10], "b": [20]}


@pytest.mark.parametrize("wrapped", [False, True])
def test_pandas_conform_value_dependent_promotion_requires_execution(wrapped):
    """Only pandas' eager fill path derives this dtype from actual nulls."""
    import narwhals as nw
    import pandas as pd
    from mountainash.core.dtypes import NativeDtype
    from mountainash.typespec.spec import FieldDefinition, TableSchema
    from mountainash.typespec.universal_types import UniversalType

    source = pd.DataFrame({"x": [1.0, None]})
    spec = TableSchema(fields={"x": FieldDefinition(type=UniversalType.ANY, null_fill="missing")})
    relation = ma.relation(nw.from_native(source) if wrapped else source).conform(spec)
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()
    dtype = relation.collect_schema(allow_execution=True)["x"]
    assert isinstance(dtype, NativeDtype)
    assert dtype.value == pd.Series([1.0, "missing"], dtype=object).dtype
    actual = relation.collect()
    if hasattr(actual, "to_native"):
        actual = actual.to_native()
    assert actual.to_dict("list") == {"x": [1.0, "missing"]}
