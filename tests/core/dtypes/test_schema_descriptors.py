"""Native metadata must survive decoding without inspecting any data rows."""
from __future__ import annotations

import ibis.expr.datatypes as dt
import narwhals as nw
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest

from mountainash.core.dtypes import NativeDtype, TypeTarget, registry
from mountainash.core.dtypes.errors import UnknownDtypeError


@pytest.mark.parametrize("native,target,precision,zone", [
    (pl.Datetime("ns", "Europe/London"), TypeTarget.POLARS, 9, "Europe/London"),
    (pa.timestamp("ms", "Europe/London"), TypeTarget.PYARROW, 3, "Europe/London"),
    (dt.Timestamp(scale=5, timezone="Europe/London"), TypeTarget.IBIS, 5, "Europe/London"),
    (nw.Datetime("us", "Europe/London"), TypeTarget.NARWHALS, 6, "Europe/London"),
    (pd.DatetimeTZDtype(unit="ns", tz="Europe/London"), TypeTarget.PANDAS, 9, "Europe/London"),
])
def test_native_timestamp_parameters_survive(native, target, precision, zone):
    actual = registry.from_native(native, target)
    assert getattr(actual, "precision", None) == precision
    assert getattr(actual, "timezone_aware", None) is True
    assert getattr(actual, "timezone", None) == zone


@pytest.mark.parametrize("native,target", [
    (pl.Datetime("us"), TypeTarget.POLARS),
    (pa.timestamp("us"), TypeTarget.PYARROW),
    (dt.Timestamp(scale=6), TypeTarget.IBIS),
    (nw.Datetime("us"), TypeTarget.NARWHALS),
])
def test_known_naive_is_not_unknown_awareness(native, target):
    actual = registry.from_native(native, target)
    assert getattr(actual, "timezone_aware", None) is False
    assert actual.timezone is None


@pytest.mark.parametrize("native,target", [
    (pl.List(pl.Struct({"at": pl.Datetime("ns", "UTC")})), TypeTarget.POLARS),
    (pa.list_(pa.struct([pa.field("at", pa.timestamp("ns", "UTC"))])), TypeTarget.PYARROW),
    (dt.Array(dt.Struct({"at": dt.Timestamp(scale=9, timezone="UTC")})), TypeTarget.IBIS),
    (nw.List(nw.Struct([nw.Field("at", nw.Datetime("ns", "UTC"))])), TypeTarget.NARWHALS),
    (pd.ArrowDtype(pa.list_(pa.struct([pa.field("at", pa.timestamp("ns", "UTC"))]))), TypeTarget.PANDAS),
])
def test_recursive_element_metadata_survives(native, target):
    actual = registry.from_native(native, target)
    element = getattr(actual, "element", None)
    fields = getattr(element, "fields", ())
    assert tuple(name for name, _ in fields) == ("at",)
    timestamp = fields[0][1]
    assert timestamp.precision == 9
    assert timestamp.timezone_aware is True
    assert timestamp.timezone == "UTC"


@pytest.mark.parametrize("native,target", [
    (pl.Array(pl.Int64, (2, 3)), TypeTarget.POLARS),
    (pa.list_(pa.list_(pa.int64(), 3), 2), TypeTarget.PYARROW),
])
def test_fixed_array_dimensions_are_not_variable_lists(native, target):
    actual = registry.from_native(native, target)
    assert getattr(actual, "dimensions", None) == (2, 3)


@pytest.mark.parametrize("native,target,unit", [
    (pl.Duration("ns"), TypeTarget.POLARS, "ns"),
    (pa.duration("ms"), TypeTarget.PYARROW, "ms"),
    (nw.Duration("us"), TypeTarget.NARWHALS, "us"),
])
def test_fixed_duration_unit_survives(native, target, unit):
    actual = registry.from_native(native, target)
    assert getattr(actual, "unit", None) == unit
    assert actual.semantics == "fixed"


def test_sql_time_precision_survives():
    actual = registry.from_native(pa.time64("us"), TypeTarget.PYARROW)
    assert getattr(actual, "precision", None) == 6


@pytest.mark.parametrize("native,target", [
    (pl.Null, TypeTarget.POLARS),
    (pa.null(), TypeTarget.PYARROW),
    (dt.null, TypeTarget.IBIS),
    (pd.Series([], dtype=object).dtype, TypeTarget.PANDAS),
    (pa.decimal256(50, 4), TypeTarget.PYARROW),
])
def test_native_only_type_is_not_lost_or_guessed(native, target):
    try:
        actual = registry.from_native(native, target)
    except UnknownDtypeError as error:
        pytest.fail(f"Native type description was discarded: {error}")
    assert isinstance(actual, NativeDtype)
    assert actual.value == native
    assert actual.target is target


@pytest.mark.parametrize("native,target", [
    (pa.field("n", pa.int64(), nullable=False), TypeTarget.PYARROW),
    (dt.Int64(nullable=False), TypeTarget.IBIS),
    (pd.Int64Dtype(), TypeTarget.PANDAS),
])
def test_native_scalar_refinements_keep_broad_classification(native, target):
    from mountainash.core.dtypes import MountainashDtype, dtype_family
    actual = registry.from_native(native, target)
    assert isinstance(actual, NativeDtype)
    assert dtype_family(actual) is MountainashDtype.I64


def test_field_qualifiers_preserve_portable_timestamp_access():
    source = pa.field("at", pa.timestamp("ns", "UTC"), nullable=False)
    actual = registry.from_native(source, TypeTarget.PYARROW)
    assert actual.precision == 9
    assert actual.timezone_aware is True
    assert actual.timezone == "UTC"
    assert actual.native.value.nullable is False
    renamed = registry.from_native(source.with_name("other"), TypeTarget.PYARROW)
    assert actual == renamed


def test_decimal_cast_retains_supported_native_encoding():
    source = pa.decimal256(12, 4)
    dtype = registry.from_native(source, TypeTarget.PYARROW)
    assert registry.to_native_cast(dtype, TypeTarget.PYARROW) == source


def test_field_qualifiers_cannot_be_silently_used_as_a_dtype():
    from mountainash.core.dtypes.errors import DtypeMappingError

    source = pa.field("at", pa.timestamp("ns", "UTC"), nullable=False)
    dtype = registry.from_native(source, TypeTarget.PYARROW)
    with pytest.raises(DtypeMappingError, match="field"):
        registry.to_native_schema(dtype, TypeTarget.PYARROW)
