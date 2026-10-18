"""Public descriptor construction retains known requirements and null shape."""
from __future__ import annotations

from datetime import datetime, timezone

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes import SchemaTypeStatus, TimestampDtype
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("value", [None, datetime(2026, 1, 1, 0, 0, 0, 123456, tzinfo=timezone.utc)])
def test_utc_literal_retains_values_and_type(backend_name, backend_factory, value):
    source = backend_factory.create({"id": [1, 2]}, backend_name)
    target = TimestampDtype(6, True, "UTC")
    result = ma.relation(source).select(ma.lit(value, dtype=target).alias("at")).to_polars()
    assert result.schema["at"] == pl.Datetime("us", "UTC")
    assert result["at"].to_list() == [value, value]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_entire_unknown_target_preserves_cast_and_infers_literal(backend_name, backend_factory):
    source = backend_factory.create({"x": [7, -3, None]}, backend_name)
    unknown = SchemaTypeStatus.UNKNOWN
    result = ma.relation(source).select(
        ma.col("x").cast(unknown).alias("x"), ma.lit(4, dtype=unknown).alias("n"),
    ).to_polars()
    original = ma.relation(source).to_polars()
    assert result.schema["x"] == original.schema["x"]
    assert result["x"].to_list() == [7, -3, None]
    assert result["n"].to_list() == [4, 4, 4]


class NativeFixedArrayExportCrash(RuntimeError):
    """An isolated native Arrow export received SIGSEGV."""


def _construction_expectation(request, backend, dtype, *, nullable=False, conditional=False, extension_decimal=False):
    from contextlib import nullcontext
    import pyarrow as pa
    from ibis.common.exceptions import UnsupportedBackendType
    from mountainash.core.dtypes import ArrayDtype, DecimalDtype, DurationDtype, ListDtype, StructDtype, TimeDtype
    from mountainash.core.dtypes.errors import DtypeMappingError
    from mountainash.core.types import BackendCapabilityError

    if isinstance(dtype, TimeDtype) and dtype.precision == 9 and backend.startswith("ibis-"):
        return pytest.raises(DtypeMappingError)
    if backend == "ibis-sqlite" and isinstance(dtype, (ListDtype, ArrayDtype, StructDtype)):
        return pytest.raises(UnsupportedBackendType)
    if extension_decimal and isinstance(dtype, DecimalDtype) and (
        backend.startswith("narwhals-") or backend in {"pandas", "ibis-sqlite"}
    ):
        return pytest.raises(BackendCapabilityError)
    if backend == "ibis-sqlite" and isinstance(dtype, TimeDtype):
        request.applymarker(pytest.mark.xfail(strict=True, raises=pa.ArrowNotImplementedError,
            reason="131: Ibis-SQLite exports time values through a duration-backed pandas column"))
    if conditional and backend == "ibis-sqlite" and isinstance(dtype, TimestampDtype) and dtype.precision == 6:
        request.applymarker(pytest.mark.xfail(strict=True, raises=AssertionError,
            reason="298: Ibis-SQLite timestamp CAST formats fractional seconds to milliseconds"))
    if isinstance(dtype, DurationDtype) and backend == "ibis-duckdb":
        request.applymarker(pytest.mark.xfail(strict=True, raises=pa.ArrowNotImplementedError,
            reason="314: Ibis-DuckDB interval Arrow export cannot cast month/day/nanosecond intervals to duration"))
    if nullable and backend in {"pandas", "narwhals-pandas"} and isinstance(dtype, (ListDtype, ArrayDtype, StructDtype)):
        request.applymarker(pytest.mark.xfail(strict=True, raises=pa.ArrowInvalid,
            reason="342: Narwhals pandas nested-null scalar broadcasting passes pd.NA to Arrow scalar inference"))
    if conditional and backend == "ibis-duckdb" and isinstance(dtype, ArrayDtype):
        import duckdb
        request.applymarker(pytest.mark.xfail(strict=True, raises=duckdb.NotImplementedException,
            reason="343: DuckDB CASE does not implement SMALLINT[2] branch results"))
    return nullcontext()


def _family_cases():
    from datetime import time, timedelta
    from decimal import Decimal
    from mountainash.core.dtypes import (
        ArrayDtype, DecimalDtype, DurationDtype, ListDtype, MountainashDtype,
        StructDtype, TimeDtype,
    )

    return [
        pytest.param(TimestampDtype(6, True, "UTC"), datetime(2026, 1, 1, microsecond=123456, tzinfo=timezone.utc),
                     pl.Datetime("us", "UTC"), id="timestamp"),
        pytest.param(TimeDtype(), time(12, 34, 56, 123456), pl.Time, id="time-default"),
        pytest.param(TimeDtype(9), time(12, 34, 56, 123456), pl.Time, id="time"),
        pytest.param(DurationDtype("us", "fixed"), timedelta(seconds=3, microseconds=123456),
                     pl.Duration("us"), id="duration"),
        pytest.param(ListDtype(MountainashDtype.I16), [1, None, -3], pl.List(pl.Int16), id="list"),
        pytest.param(ArrayDtype(MountainashDtype.I16, (2,)), [1, -3],
                     pl.Array(pl.Int16, 2), id="array"),
        pytest.param(StructDtype((("count", MountainashDtype.I16), ("at", TimestampDtype(6, True, "UTC")))),
                     {"count": 7, "at": datetime(2026, 1, 1, microsecond=123456, tzinfo=timezone.utc)},
                     pl.Struct({"count": pl.Int16, "at": pl.Datetime("us", "UTC")}), id="struct"),
        pytest.param(DecimalDtype(10, 3), Decimal("0.004"), pl.Decimal(10, 3), id="decimal"),
    ]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("dtype,value,native", _family_cases())
@pytest.mark.parametrize("null", [False, True])
@pytest.mark.parametrize("rows", [0, 2])
def test_parameterized_literal_family(backend_name, backend_factory, dtype, value, native, null, rows, request):
    from mountainash.core.dtypes import ListDtype, StructDtype
    from mountainash.core.dtypes import ArrayDtype
    if rows == 0 and not null and backend_name in {"pandas", "narwhals-pandas"} and isinstance(dtype, (ListDtype, ArrayDtype, StructDtype)):
        request.applymarker(pytest.mark.xfail(strict=True, raises=ValueError,
            reason="348: Narwhals constructs a one-element nested literal against an empty pandas index"))

    if isinstance(dtype, ArrayDtype) and backend_name == "ibis-polars" and (null or rows == 0):
        # Isolate a demonstrated native Arrow export segfault from the test runner.
        import subprocess
        import sys
        if null and rows:
            request.applymarker(pytest.mark.xfail(strict=True, raises=NativeFixedArrayExportCrash,
                reason="344: PyArrow crashes converting the Ibis-Polars null LargeListArray to a fixed-size list"))

        script = f"""
import ibis
import polars as pl
import mountainash as ma
from mountainash.core.dtypes import ArrayDtype, MountainashDtype
source = ibis.polars.connect().create_table("input", pl.DataFrame({{"id": [1, 2]}}))
out = ma.relation(source).head({rows}).select(ma.col("id"), ma.lit({None if null else [1, -3]!r}, dtype=ArrayDtype(MountainashDtype.I16, (2,))).alias("value")).to_polars()
assert out.schema["value"] == pl.Array(pl.Int16, 2)
assert out["value"].to_list() == {[None if null else [1, -3]] * rows!r}
"""
        child = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        if child.returncode == -11:
            raise NativeFixedArrayExportCrash("typed-null fixed-array export received SIGSEGV")
        assert child.returncode == 0, f"isolated native export exited {child.returncode}: {child.stderr}"
        return
    source = backend_factory.create({"id": [1, 2]}, backend_name)
    value = None if null else value
    with _construction_expectation(request, backend_name, dtype, nullable=null):
        out = ma.relation(source).head(rows).select(ma.col("id"), ma.lit(value, dtype=dtype).alias("value")).to_polars()
        assert out.schema["value"] == native
        assert out["value"].to_list() == [value] * rows


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_unknown_cast_and_literal_compose_without_losing_operand_metadata(backend_name, backend_factory):
    source = backend_factory.create({"x": [7, -3, None]}, backend_name)
    out = ma.relation(source).select(
        ma.col("x").cast(SchemaTypeStatus.UNKNOWN).is_null().alias("missing"),
        ma.when(ma.col("x").is_null()).then(ma.lit(4, dtype=SchemaTypeStatus.UNKNOWN))
        .otherwise(ma.col("x").cast(SchemaTypeStatus.UNKNOWN)).alias("filled"),
    ).to_polars()
    assert out.to_dict(as_series=False) == {
        "missing": [False, False, True], "filled": [7, -3, 4],
    }


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("empty", [False, True])
def test_partial_cast_after_join_preserves_source_nanoseconds(backend_name, backend_factory, empty):
    import numpy as np

    integers = [] if empty else [1767225600123456789, 1767225600987654321]
    ids = np.arange(len(integers), dtype=np.int64)
    if backend_name.startswith("ibis-"):
        import ibis
        import pyarrow as pa
        from fixtures.backend_registry import create_ibis_sqlite_table

        connection = getattr(ibis, backend_name.removeprefix("ibis-")).connect()
        left = pa.table({"id": pa.array(ids), "at": pa.array(integers, type=pa.timestamp("ns"))})
        right = pa.table({"id": [0, 1]})
        if backend_name == "ibis-sqlite":
            source = create_ibis_sqlite_table(connection, "left_input", left)
            other = create_ibis_sqlite_table(connection, "right_input", right)
        else:
            source = connection.create_table("left_input", left)
            other = connection.create_table("right_input", right)
    else:
        source, other = backend_factory.create_pair(
            {"id": ids, "at": np.array(integers, dtype="datetime64[ns]")},
            {"id": np.array([0, 1], dtype=np.int64)}, backend_name,
        )
    target = TimestampDtype(timezone_aware=False, timezone=None)
    try:
        out = ma.relation(source).join(other, on="id").sort("id").select(ma.col("at").cast(target)).to_polars()
        assert out.schema["at"] == pl.Datetime("ns")
        assert out["at"].cast(pl.Int64).to_list() == integers
        assert target.precision is SchemaTypeStatus.UNKNOWN
    finally:
        if backend_name.startswith("ibis-"):
            connection.disconnect()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("dtype,value,native", _family_cases())
@pytest.mark.parametrize("route", ["extension", "substrait"])
def test_parameterized_cast_routes_compose(backend_name, backend_factory, dtype, value, native, route, request):
    from mountainash.core.dtypes import DecimalDtype
    from mountainash.expressions.core.expression_api.api_builders.substrait.api_bldr_cast import SubstraitCastAPIBuilder

    source = backend_factory.create({"id": [1, 2]}, backend_name)
    operand = ma.lit(value)
    if route == "substrait":
        converted = SubstraitCastAPIBuilder(operand).cast(dtype)
    else:
        options = {"rounding": "half_to_even"} if isinstance(dtype, DecimalDtype) else {}
        converted = operand.cast(dtype, **options)
    expression = ma.when(ma.col("id").eq(1)).then(ma.lit(None, dtype=dtype)).otherwise(converted)
    with _construction_expectation(
        request, backend_name, dtype, nullable=True, conditional=True,
        extension_decimal=route == "extension",
    ):
        out = ma.relation(source).select(ma.col("id"), expression.alias("value")).to_polars()
        assert out.schema["value"] == native
        assert out["value"].to_list() == [None, value]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_partial_cast_compilation_does_not_probe_source_rows(backend_name, backend_factory, monkeypatch):
    import ibis
    import narwhals as nw
    from ibis.common.deferred import Deferred

    value = datetime(2026, 1, 1, microsecond=123456, tzinfo=timezone.utc)
    source = backend_factory.create({"at": [value]}, backend_name)
    expr = ma.col("at").cast(TimestampDtype(timezone_aware=True, timezone="UTC"))

    def forbidden(*args, **kwargs):
        raise AssertionError("cast construction attempted a data/schema projection or execution")

    with monkeypatch.context() as patch:
        patch.setattr(pl.LazyFrame, "collect", forbidden)
        patch.setattr(pl.LazyFrame, "collect_schema", forbidden)
        patch.setattr(ibis.expr.types.Table, "execute", forbidden)
        patch.setattr(ibis.expr.types.Table, "to_pyarrow", forbidden)
        patch.setattr(ibis.expr.types.Table, "select", forbidden)
        patch.setattr(nw.DataFrame, "select", forbidden)
        compiled = expr.compile(source)
        if isinstance(compiled, Deferred):
            compiled.resolve(source)
    out = ma.relation(source).select(expr).to_polars()
    assert out.schema["at"] == pl.Datetime("us", "UTC")
    assert out["at"].to_list() == [value]


def test_partial_narwhals_cast_lowers_recursive_owned_native_override():
    import narwhals as nw
    from mountainash.core.dtypes import NativeDtype, StructDtype, TypeTarget

    source = nw.from_native(pl.DataFrame({
        "value": [{"a": "2026-01-01T00:00:00Z", "b": 1}],
    }))
    target = StructDtype((
        ("a", TimestampDtype(timezone_aware=True, timezone="UTC", native=NativeDtype(
            value=nw.Datetime(time_unit="us", time_zone="UTC"), target=TypeTarget.NARWHALS,
        ))),
        ("b", SchemaTypeStatus.UNKNOWN),
    ))
    result = ma.relation(source).select(ma.col("value").cast(target).alias("value")).to_polars()
    assert result.schema["value"] == pl.Struct({
        "a": pl.Datetime("us", "UTC"), "b": pl.Int64,
    })
    assert result["value"].to_list() == [{
        "a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": 1,
    }]


def test_partial_narwhals_cast_rejects_foreign_polars_native_override():
    import narwhals as nw
    from mountainash.core.dtypes import NativeDtype, StructDtype, TypeTarget
    from mountainash.core.dtypes.errors import DtypeMappingError

    source = nw.from_native(pl.DataFrame({"value": [{"a": "2026-01-01", "b": 1}]}))
    target = StructDtype((
        ("a", TimestampDtype(timezone_aware=True, timezone="UTC", native=NativeDtype(
            value=pl.Datetime("us", "UTC"), target=TypeTarget.POLARS,
        ))),
        ("b", SchemaTypeStatus.UNKNOWN),
    ))
    with pytest.raises(DtypeMappingError):
        ma.relation(source).select(ma.col("value").cast(target)).to_polars()
