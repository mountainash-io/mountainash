"""Partial parameterized targets inherit only compatible literal/source evidence."""
from __future__ import annotations

from datetime import datetime, timezone

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes import (
    ListDtype, MountainashDtype, SchemaTypeStatus, StructDtype, TimestampDtype,
)
from fixtures.backend_registry import ALL_BACKENDS


def test_partial_timestamp_literal_cast_preserves_native_precision():
    import pandas as pd
    import narwhals as nw

    value = pd.Timestamp("2026-01-01 00:00:00.123456789")
    target = TimestampDtype(timezone_aware=False, timezone=None)
    source = nw.from_native(pd.DataFrame({"id": [1]}))
    result = ma.relation(source).select(
        ma.lit(value, dtype=target).cast(target).alias("at")
    ).to_polars()
    assert result.schema["at"] == pl.Datetime("ns")
    assert result["at"].cast(pl.Int64).item() == value.value

@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_partial_timestamp_literal_infers_value_precision(backend_name, backend_factory):
    value = datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=timezone.utc)
    source = backend_factory.create({"id": [1]}, backend_name)
    target = TimestampDtype(timezone_aware=True, timezone="UTC")
    result = ma.relation(source).select(ma.lit(value, dtype=target).alias("at")).to_polars()
    assert result["at"].to_list() == [value]
    assert target.precision is SchemaTypeStatus.UNKNOWN


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_partial_list_literal_inherits_native_child_type(backend_name, backend_factory):
    source = backend_factory.create({"id": [1]}, backend_name)
    target = ListDtype()
    if backend_name == "ibis-sqlite":
        from ibis.common.exceptions import UnsupportedBackendType
        with pytest.raises(UnsupportedBackendType):
            ma.relation(source).select(ma.lit([2**40, None, -3], dtype=target).alias("items")).to_polars()
        return
    result = ma.relation(source).select(ma.lit([2**40, None, -3], dtype=target).alias("items")).to_polars()
    assert result.schema["items"] == pl.List(pl.Int64)
    assert result["items"].to_list() == [[2**40, None, -3]]
    assert target.element is SchemaTypeStatus.UNKNOWN


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_partial_struct_literal_preserves_known_child_and_infers_unknown_field(backend_name, backend_factory):
    source = backend_factory.create({"id": [1]}, backend_name)
    target = StructDtype((("count", MountainashDtype.I16), ("flag", SchemaTypeStatus.UNKNOWN)))
    expression = ma.lit({"count": 7, "flag": True}, dtype=target).alias("item")
    if backend_name == "ibis-sqlite":
        from ibis.common.exceptions import UnsupportedBackendType
        with pytest.raises(UnsupportedBackendType):
            ma.relation(source).select(expression).to_polars()
        return
    result = ma.relation(source).select(expression).to_polars()
    assert result.schema["item"] == pl.Struct({"count": pl.Int16, "flag": pl.Boolean})
    assert result["item"].to_list() == [{"count": 7, "flag": True}]
    assert target.fields[1][1] is SchemaTypeStatus.UNKNOWN


@pytest.mark.parametrize("provider", ["arrow", "duckdb"])
@pytest.mark.parametrize("nested", [False, True])
def test_narwhals_partial_time_uses_provider_metadata(provider, nested):
    # These additional native providers are not in ALL_BACKENDS.
    from datetime import time
    import duckdb
    import narwhals as nw
    import pyarrow as pa
    from mountainash.core.dtypes import TimeDtype

    value = time(12, 34, 56, 123456)
    target = ListDtype(TimeDtype()) if nested else TimeDtype()
    literal = [value, None] if nested else value
    source = pa.table({"id": [1, 2]})
    with duckdb.connect() as connection:
        wrapped = nw.from_native(connection.from_arrow(source) if provider == "duckdb" else source)
        result = ma.relation(wrapped).select(ma.lit(literal, dtype=target).alias("clock")).to_polars()
    assert result.schema["clock"] == (pl.List(pl.Time) if nested else pl.Time)
    assert result["clock"].to_list() == [literal, literal]
    assert (target.element if nested else target).precision is SchemaTypeStatus.UNKNOWN
