# tests/expressions/cross_backend/test_native_dtype_passthrough.py
"""NativeDtype passthrough: parameterized casts on the owning backend,
precise errors cross-backend, bare-container casts raise."""
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes import DtypeMappingError


def test_parameterized_cast_on_owning_backend():
    df = pl.DataFrame({"ts": ["2024-01-01T00:00:00"]})
    result = (
        ma.relation(df)
        .with_columns(ma.col("ts").cast(pl.Datetime("us")).alias("t"))
        .to_polars()
    )
    assert result.schema["t"] == pl.Datetime("us")


def test_native_dtype_on_foreign_backend_raises():
    import pandas as pd
    df = pd.DataFrame({"x": [1, 2]})
    expr = ma.col("x").cast(pl.Datetime("us"))
    with pytest.raises(DtypeMappingError, match="polars"):
        ma.relation(df).with_columns(expr.alias("t")).collect()


def test_bare_list_cast_raises():
    df = pl.DataFrame({"x": ["a"]})
    expr = ma.col("x").cast("list")
    with pytest.raises(DtypeMappingError, match="cast target"):
        ma.relation(df).with_columns(expr.alias("y")).to_polars()
