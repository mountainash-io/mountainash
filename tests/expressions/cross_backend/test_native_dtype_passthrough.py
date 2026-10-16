# tests/expressions/cross_backend/test_native_dtype_passthrough.py
"""NativeDtype passthrough: parameterized casts on the owning backend,
precise errors cross-backend, bare-container casts raise."""
from datetime import date, datetime, time, timezone
import polars as pl
import pytest

import mountainash as ma
from mountainash.core.dtypes import DtypeMappingError


@pytest.mark.parametrize("lazy", [False, True])
def test_native_list_date_cast_preserves_null_shape(lazy):
    """Temporal native dtype casts preserve null parents and null leaves."""
    frame = pl.DataFrame(
        {"x": [["2026-10-12", None], None, []]},
        schema={"x": pl.List(pl.String)},
    )
    source = frame.lazy() if lazy else frame
    result = ma.relation(source).select(
        ma.col("x").cast(pl.List(pl.Date)).alias("days")
    ).to_polars()
    assert result.schema["days"] == pl.List(pl.Date)
    assert result["days"].to_list() == [[date(2026, 10, 12), None], None, []]


@pytest.mark.parametrize(
    ("values", "dtype", "expected"),
    [
        ([0, 1, None], pl.Date, [date(1970, 1, 1), date(1970, 1, 2), None]),
        (
            ["2024-01-02T03:04:05.123456", None],
            pl.Datetime("ms"),
            [datetime(2024, 1, 2, 3, 4, 5, 123000), None],
        ),
        (
            ["2024-01-02T03:04:05.123456+02:00"],
            pl.Datetime("us", "UTC"),
            [datetime(2024, 1, 2, 1, 4, 5, 123456, tzinfo=timezone.utc)],
        ),
    ],
)
def test_native_temporal_cast_uses_epoch_unit_and_explicit_timezone(values, dtype, expected):
    frame = pl.DataFrame({"x": values})
    result = ma.relation(frame).select(ma.col("x").cast(dtype).alias("out")).to_polars()
    assert result.schema["out"] == dtype
    assert result["out"].to_list() == expected


@pytest.mark.parametrize("failure_behavior", ["throw", "null"])
def test_native_datetime_zoned_target_rejects_naive_source(failure_behavior):
    frame = pl.DataFrame({"x": ["2026-10-12T01:02"]})
    expr = ma.col("x").cast(
        pl.Datetime("us", "UTC"), failure_behavior=failure_behavior
    ).alias("out")
    if failure_behavior == "throw":
        with pytest.raises(pl.exceptions.InvalidOperationError):
            ma.relation(frame).select(expr).to_polars()
    else:
        result = ma.relation(frame).select(expr).to_polars()
        assert result["out"].to_list() == [None]


@pytest.mark.parametrize("failure_behavior", ["throw", "null"])
def test_native_time_cast_parses_valid_value_and_handles_invalid(failure_behavior):
    frame = pl.DataFrame({"x": ["01:02:03", "not-time", None]})
    expr = ma.col("x").cast(pl.Time, failure_behavior=failure_behavior).alias("out")
    if failure_behavior == "throw":
        with pytest.raises(pl.exceptions.InvalidOperationError):
            ma.relation(frame).select(expr).to_polars()
    else:
        result = ma.relation(frame).select(expr).to_polars()
        assert result.schema["out"] == pl.Time
        assert result["out"].to_list() == [time(1, 2, 3), None, None]


def test_native_array_temporal_cast_preserves_width_and_nulls():
    frame = pl.DataFrame(
        {"x": [["2026-10-12", None], None]},
        schema={"x": pl.Array(pl.String, 2)},
    )
    result = ma.relation(frame).select(
        ma.col("x").cast(pl.Array(pl.Date, 2)).alias("days")
    ).to_polars()
    assert result.schema["days"] == pl.Array(pl.Date, 2)
    assert result["days"].to_list() == [[date(2026, 10, 12), None], None]


@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize(
    ("source_dtype", "target_dtype", "values", "expected"),
    [
        (
            pl.List(pl.String), pl.List(pl.Datetime),
            [["2026-10-12T01:02:03", None], None, []],
            [[datetime(2026, 10, 12, 1, 2, 3), None], None, []],
        ),
        (
            pl.Struct({"ts": pl.String}), pl.Struct({"ts": pl.Datetime}),
            [{"ts": "2026-10-12T01:02:03"}, None],
            [{"ts": datetime(2026, 10, 12, 1, 2, 3)}, None],
        ),
    ],
)
def test_native_nested_bare_datetime_cast(lazy, source_dtype, target_dtype, values, expected):
    frame = pl.DataFrame({"x": values}, schema={"x": source_dtype})
    result = ma.relation(frame.lazy() if lazy else frame).select(
        ma.col("x").cast(target_dtype).alias("out")
    ).to_polars()
    assert result.schema["out"] == target_dtype
    assert result["out"].to_list() == expected


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["polars", "polars-lazy", "narwhals-polars", "narwhals-lazy"])
@pytest.mark.parametrize("aggregate_first", [False, True])
def test_temporal_cast_composes_with_partitioned_minimum(backend_name, backend_factory, aggregate_first):
    source = backend_factory.create(
        {"x": ["2026-10-12", "2026-10-10", "2026-10-14"], "group": ["a", "a", "b"]},
        backend_name,
    )
    expression = ma.col("x").min().cast("date") if aggregate_first else ma.col("x").cast("date").min()
    result = ma.relation(source).select(
        expression.over("group").alias("out")
    ).to_polars()
    assert result.schema["out"] == pl.Date
    assert result["out"].to_list() == [date(2026, 10, 10), date(2026, 10, 10), date(2026, 10, 14)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["polars", "polars-lazy", "narwhals-polars", "narwhals-lazy"])
def test_temporal_cast_composes_with_ordered_lag_predicate(backend_name, backend_factory):
    source = backend_factory.create(
        {"x": ["2026-10-12", "2026-10-13"], "group": ["a", "a"], "seq": [2, 1]},
        backend_name,
    )
    result = ma.relation(source).select(
        ma.col("x").cast("date").lag().is_null().over("group", order_by="seq").alias("out")
    ).to_polars()
    assert result["out"].to_list() == [False, True]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["polars", "polars-lazy", "narwhals-polars", "narwhals-lazy"])
def test_temporal_cast_windows_comparison_operand(backend_name, backend_factory):
    source = backend_factory.create(
        {
            "x": ["2026-10-12", "2026-10-10", "2026-10-14"],
            "other": [date(2026, 10, 11), date(2026, 10, 10), date(2026, 10, 14)],
            "group": ["a", "a", "b"],
        },
        backend_name,
    )
    result = ma.relation(source).select(
        ma.col("x").cast("date").eq(ma.col("other").min()).over("group").alias("out")
    ).to_polars()
    assert result["out"].to_list() == [False, True, True]


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
