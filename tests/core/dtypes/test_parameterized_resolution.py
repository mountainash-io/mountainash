"""Partial target intent must not be confused with missing source evidence."""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import canonical as c

U = c.SchemaTypeStatus.UNKNOWN
D = c.MountainashDtype


@pytest.mark.parametrize("target,source,expected", [
    (c.TimestampDtype(timezone_aware=True, timezone="UTC"),
     c.TimestampDtype(9, True, "Europe/London"), c.TimestampDtype(9, True, "UTC")),
    (c.TimestampDtype(6), c.TimestampDtype(9, False, None), c.TimestampDtype(6, False, None)),
    (c.TimestampDtype(timezone_aware=False), c.TimestampDtype(9, True, "UTC"),
     c.TimestampDtype(9, False, None)),
    (c.TimestampDtype(timezone="UTC"), c.TimestampDtype(9, False, None),
     c.TimestampDtype(9, True, "UTC")),
    (c.TimestampDtype(timezone_aware=True, timezone=None), c.TimestampDtype(9, True, "Asia/Tokyo"),
     c.TimestampDtype(9, True, None)),
    (c.TimeDtype(), c.TimeDtype(6), c.TimeDtype(6)),
    (c.DurationDtype(semantics="calendar"), c.DurationDtype("ns", "fixed"),
     c.DurationDtype(semantics="calendar")),
    (c.DurationDtype("ms"), c.DurationDtype("ns", "fixed"), c.DurationDtype("ms", "fixed")),
    (c.ListDtype(), c.ListDtype(c.TimestampDtype(9, True, "UTC")),
     c.ListDtype(c.TimestampDtype(9, True, "UTC"))),
    (c.ArrayDtype(D.I16), c.ArrayDtype(D.I64, (2, 3)), c.ArrayDtype(D.I16, (2, 3))),
    (c.StructDtype((("a", U), ("b", D.I16))),
     c.StructDtype((("b", D.STRING), ("a", c.TimeDtype(9)), ("extra", D.BOOL))),
     c.StructDtype((("a", c.TimeDtype(9)), ("b", D.I16)))),
    (c.ListDtype(), c.StructDtype((("a", D.I16),)), c.ListDtype()),
    (U, c.TimestampDtype(9, True, "UTC"), U),
])
def test_partial_resolution_keeps_known_requirements(target, source, expected):
    before = repr(target)
    assert c.resolve_dtype_parameters(target, source) == expected
    assert repr(target) == before


@pytest.mark.parametrize("source", [U, c.SchemaTypeStatus.UNCONSTRAINED, None])
def test_missing_source_evidence_does_not_resolve_target(source):
    target = c.TimestampDtype(timezone_aware=True, timezone="UTC")
    result = c.resolve_dtype_parameters(target, source)
    assert result == target
    assert result.precision is U


def test_inherited_child_does_not_acquire_source_native_authority():
    import polars as pl
    from mountainash.core.dtypes import NativeDtype, TypeTarget

    source = c.ListDtype(c.TimestampDtype(
        9, True, "UTC", native=NativeDtype(value=pl.Datetime("ns", "UTC"), target=TypeTarget.POLARS),
    ))
    resolved = c.resolve_dtype_parameters(c.ListDtype(), source)
    assert resolved == c.ListDtype(c.TimestampDtype(9, True, "UTC"))


@pytest.mark.parametrize("target", [c.TimestampDtype(), c.ListDtype(), U])
def test_cast_parser_accepts_partial_targets(target):
    assert c.parse_cast_target(target) == target


@pytest.mark.parametrize("precision,unit", [(0, "s"), (3, "ms"), (6, "us"), (9, "ns")])
def test_pandas_naive_timestamp_preserves_unit_without_timezone(precision, unit):
    import pandas as pd
    from mountainash.core.dtypes import TypeTarget, registry

    native = registry.to_native_schema(c.TimestampDtype(precision, False, None), TypeTarget.PANDAS)
    result = pd.Series(["2026-01-01T00:00:00", None], dtype=native)
    assert str(result.dtype) == f"datetime64[{unit}]"
    assert result.dt.tz is None
    assert result.iloc[0] == pd.Timestamp("2026-01-01")
    assert pd.isna(result.iloc[1])


def test_pandas_nested_native_child_retains_owning_target():
    import pandas as pd
    import pyarrow as pa
    from mountainash.core.dtypes import TypeTarget, registry

    child = c.NativeDtype(value=pd.Int16Dtype(), target=TypeTarget.PANDAS)
    target = c.StructDtype((("n", c.ListDtype(child)),))
    native = registry.to_native_schema(target, TypeTarget.PANDAS)
    result = pd.Series([{"n": [1, None, -3]}, None], dtype=native)
    assert native == pd.ArrowDtype(pa.struct([("n", pa.list_(pa.int16()))]))
    assert result.array.__arrow_array__().to_pylist() == [{"n": [1, None, -3]}, None]
