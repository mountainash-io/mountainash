"""Aggregate schema metadata must match native execution across backends."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.dtypes import MountainashDtype as D, dtype_family
from fixtures.backend_registry import ALL_BACKENDS, REGISTRY

SCHEMA_BACKENDS = [*ALL_BACKENDS, "pyarrow", "narwhals-pyarrow"]


def _source(backend_name, data, name):
    if backend_name in {"pyarrow", "narwhals-pyarrow"}:
        import pyarrow as pa
        table = pa.table(data)
        if backend_name == "narwhals-pyarrow":
            import narwhals as nw
            return nw.from_native(table)
        return table
    return REGISTRY[backend_name].build(data, name)


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
@pytest.mark.parametrize("grouped", [False, True])
def test_numeric_aggregate_schema_matches_native_output(backend_name, grouped):
    source = _source(backend_name, {"group": [0, 0, 1], "value": [2, 4, 8]}, "schema_aggregate")
    keys = ["group"] if grouped else []
    relation = ma.relation(source).group_by(*keys).agg(
        ma.col("value").sum().alias("total"),
        ma.col("value").count().alias("count"),
        ma.col("value").mean().alias("mean"),
    )

    if not grouped and backend_name in {"pyarrow", "narwhals-pyarrow"}:
        from mountainash.exceptions import IncompleteSchemaError
        with pytest.raises(IncompleteSchemaError):
            relation.collect_schema()
        schema = relation.collect_schema(allow_execution=True)
    else:
        schema = relation.collect_schema()
    assert list(schema) == [*keys, "total", "count", "mean"]
    if backend_name == "ibis-duckdb":
        from mountainash.core.dtypes import NativeDtype
        assert isinstance(schema["total"], NativeDtype)
        connection = source._find_backend(use_default=False)
        assert connection.con.sqltype(schema["total"].value) == connection.con.sqltype("HUGEINT")
    else:
        assert dtype_family(schema["total"]) is D.I64
    count_dtype = D.U32 if backend_name in {
        "polars", "polars-lazy", "narwhals-polars", "narwhals-lazy",
    } else D.I64
    assert dtype_family(schema["count"]) is count_dtype
    assert dtype_family(schema["mean"]) is D.FP64
    if grouped:
        assert relation.sort("group").to_dicts() == [
            {"group": 0, "total": 6, "count": 2, "mean": 3.0},
            {"group": 1, "total": 8, "count": 1, "mean": 8.0},
        ]
    else:
        assert relation.to_dicts() == [{"total": 14, "count": 3, "mean": 14 / 3}]


@pytest.mark.parametrize("backend_name", SCHEMA_BACKENDS)
def test_empty_global_extrema_remain_unqualified(backend_name):
    source = _source(backend_name, {"value": [2, 4]}, "schema_empty_extrema")
    relation = ma.relation(source).filter(ma.col("value") < 0).group_by().agg(
        ma.col("value").min().alias("minimum")
    )
    from mountainash.exceptions import IncompleteSchemaError

    from mountainash.core.dtypes import NativeDtype, TypeTarget
    if backend_name in {"pandas", "narwhals-pandas", "pyarrow", "narwhals-pyarrow"}:
        with pytest.raises(IncompleteSchemaError):
            relation.collect_schema()
    if backend_name in {"pandas", "narwhals-pandas"}:
        expected = D.FP64
    elif backend_name in {"pyarrow", "narwhals-pyarrow"}:
        import narwhals as nw
        import pyarrow as pa
        # Narwhals 2.28.0 types an empty PyArrow min() as the input dtype
        # (matching the other backends); 2.27.1 reported null.
        expected = (D.I64 if tuple(map(int, nw.__version__.split(".")[:2])) >= (2, 28)
                    else NativeDtype(value=pa.null(), target=TypeTarget.PYARROW))
    elif backend_name == "ibis-sqlite":
        import ibis.expr.datatypes as dt
        expected = NativeDtype(value=dt.null, target=TypeTarget.IBIS)
        assert relation.collect_schema()["minimum"] == expected
    else:
        expected = D.I64
        assert relation.collect_schema()["minimum"] == expected
    schema = relation.collect_schema(allow_execution=True)
    assert schema["minimum"] == expected
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
