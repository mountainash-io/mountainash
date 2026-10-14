"""Aggregate schema metadata must match native execution across backends."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D, dtype_family
from fixtures.backend_registry import ALL_BACKENDS, REGISTRY


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_numeric_aggregate_schema_uses_native_empty_prototype(backend_name):
    source = REGISTRY[backend_name].build({"group": [0, 0, 1], "value": [2, 4, 8]}, "schema_aggregate")
    relation = ma.relation(source).group_by().agg(
        ma.col("value").sum().alias("total"),
        ma.col("value").count().alias("count"),
        ma.col("value").mean().alias("mean"),
    )

    schema = relation.collect_schema()
    assert list(schema) == ["total", "count", "mean"]
    assert dtype_family(schema["total"]) is D.I64
    count_dtype = D.U32 if backend_name in {
        "polars", "polars-lazy", "narwhals-polars", "narwhals-lazy",
    } else D.I64
    assert dtype_family(schema["count"]) is count_dtype
    assert dtype_family(schema["mean"]) is D.FP64
    assert relation.to_dicts() == [{"total": 14, "count": 3, "mean": 14 / 3}]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_empty_global_extrema_remain_unqualified(backend_name):
    source = REGISTRY[backend_name].build({"value": [2, 4]}, "schema_empty_extrema")
    relation = ma.relation(source).filter(ma.col("value") < 0).group_by().agg(
        ma.col("value").min().alias("minimum")
    )
    from mountainash.exceptions import IncompleteSchemaError

    if backend_name in {"pandas", "narwhals-pandas"}:
        with pytest.raises(IncompleteSchemaError):
            relation.collect_schema()
        expected = D.FP64
    else:
        expected = D.I64
        assert dtype_family(relation.collect_schema()["minimum"]) is expected
    schema = relation.collect_schema(allow_execution=True)
    assert dtype_family(schema["minimum"]) is expected
    assert relation.to_dicts() == [{"minimum": None}]


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("dtype", ["Int64", "Float64", "int64[pyarrow]"])
def test_nullable_pandas_mean_does_not_certify_empty_object_dtype(dtype, wrapped):
    """pandas nullable reductions have a value-dependent scalar carrier dtype."""
    import narwhals as nw
    import pandas as pd
    from mountainash.core.dtypes import SchemaTypeStatus
    from mountainash.exceptions import IncompleteSchemaError

    source = pd.DataFrame({"n": pd.Series([2, 4], dtype=dtype)})
    relation = ma.relation(nw.from_native(source) if wrapped else source).group_by().agg(
        ma.col("n").mean().alias("average")
    )
    assert relation.schema == {"average": SchemaTypeStatus.UNKNOWN}
    with pytest.raises(IncompleteSchemaError):
        relation.collect_schema()
    assert dtype_family(relation.collect_schema(allow_execution=True)["average"]) is D.FP64
    assert relation.to_dict() == {"average": [3.0]}
