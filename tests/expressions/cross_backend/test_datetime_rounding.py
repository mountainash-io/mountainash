"""Cross-backend results for dt.round_temporal / dt.round_calendar (item 74).

Both ops share the real Substrait 9-unit domain (YEAR..MICROSECOND, no per-op
split). round_temporal declares YEAR/MONTH/WEEK UNSUPPORTED (ambiguous
fixed-duration length in v1); round_calendar covers all nine. See
2026-08-15-round-temporal-calendar-real-implementation-design.md.

Known per-dialect gaps:
- ibis-sqlite: sub-day temporal rounding and calendar multiples greater than
  one have no native implementation.
- ibis-polars: MONTH/YEAR calendar FLOOR is supported; CEIL and tie modes
  require unavailable calendar-interval addition.
"""

from __future__ import annotations

from datetime import datetime

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)

TEMPORAL_BACKENDS = [
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
]

# ibis-sqlite has no HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND truncate
# support at all (capabilities/datetime/rounding.py) -- every HOUR-based
# round_temporal case below is UNSUPPORTED there.
HOUR_CAPABLE_BACKENDS = [b for b in TEMPORAL_BACKENDS if b != "ibis-sqlite"]

# ibis-polars supports calendar FLOOR for MONTH/YEAR, but cannot add a
# calendar interval for CEIL or nearest rounding. ibis-sqlite has no
# TimestampBucket rule, so multiple > 1 is unsupported there for every unit.
MONTH_YEAR_CAPABLE_BACKENDS = [b for b in TEMPORAL_BACKENDS if b != "ibis-polars"]
QUARTER_MULTIPLE_CAPABLE_BACKENDS = [
    b for b in TEMPORAL_BACKENDS if b not in ("ibis-polars", "ibis-sqlite")
]

# 2026-03-15 10:30:00 -- an exact tie point at the hour granularity (10:30:00
# is the midpoint of [10:00, 11:00)) and non-boundary at every finer/coarser
# granularity, so FLOOR/CEIL/tie-mode all produce distinct, unambiguous
# results across DAY/HOUR and MONTH/YEAR/WEEK.
_TIE_DATA = {"ts": [datetime(2026, 3, 15, 10, 30, 0)]}
_MULTI_DATA = {"ts": [datetime(2026, 3, 15, 10, 30, 0)]}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestRoundTemporalFloorCeilDay:
    """DAY is supported on every backend, including ibis-sqlite."""

    def test_floor_day(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_temporal(rounding="FLOOR", unit="DAY")
        )
        assert actual == [datetime(2026, 3, 15, 0, 0, 0)]

    def test_ceil_day(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_temporal(rounding="CEIL", unit="DAY")
        )
        assert actual == [datetime(2026, 3, 16, 0, 0, 0)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", HOUR_CAPABLE_BACKENDS)
class TestRoundTemporalFloorCeilHour:
    def test_floor_hour(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_temporal(rounding="FLOOR", unit="HOUR")
        )
        assert actual == [datetime(2026, 3, 15, 10, 0, 0)]

    def test_ceil_hour(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_temporal(rounding="CEIL", unit="HOUR")
        )
        assert actual == [datetime(2026, 3, 15, 11, 0, 0)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", HOUR_CAPABLE_BACKENDS)
class TestRoundTemporalTieBreaking:
    """10:30:00 is exactly the midpoint of the [10:00, 11:00) hour bucket."""

    def test_tie_down_ties_to_earlier(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_temporal(rounding="ROUND_TIE_DOWN", unit="HOUR")
        )
        assert actual == [datetime(2026, 3, 15, 10, 0, 0)]

    def test_tie_up_ties_to_later(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_temporal(rounding="ROUND_TIE_UP", unit="HOUR")
        )
        assert actual == [datetime(2026, 3, 15, 11, 0, 0)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", HOUR_CAPABLE_BACKENDS)
class TestRoundTemporalMultiple:
    def test_floor_multiple_two_hours(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_MULTI_DATA, backend_name)
        actual = collect_expr(
            df,
            ma.col("ts").dt.round_temporal(rounding="FLOOR", unit="HOUR", multiple=2),
        )
        assert actual == [datetime(2026, 3, 15, 10, 0, 0)]

    def test_ceil_multiple_two_hours(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_MULTI_DATA, backend_name)
        actual = collect_expr(
            df,
            ma.col("ts").dt.round_temporal(rounding="CEIL", unit="HOUR", multiple=2),
        )
        assert actual == [datetime(2026, 3, 15, 12, 0, 0)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestRoundTemporalYearMonthWeekUnsupported:
    """v1 scope: round_temporal declares YEAR/MONTH/WEEK UNSUPPORTED on
    every backend (ambiguous fixed-duration length); round_calendar (below)
    covers them."""

    @pytest.mark.parametrize("unit", ["YEAR", "MONTH", "WEEK"])
    def test_raises_capability_error(self, backend_name, unit, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        expr = ma.col("ts").dt.round_temporal(rounding="FLOOR", unit=unit)
        with pytest.raises(BackendCapabilityError) as raised:
            collect_expr(df, expr)
        assert raised.value.function_key is FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["ibis-sqlite"])
class TestRoundTemporalSqliteSubDayUnsupported:
    """ibis-sqlite has no HOUR/MINUTE/SECOND/MILLISECOND/MICROSECOND
    TimestampTruncate support at all -- every round_temporal case above
    that isn't DAY is UNSUPPORTED there."""

    @pytest.mark.parametrize("rounding", ["FLOOR", "CEIL", "ROUND_TIE_DOWN", "ROUND_TIE_UP"])
    def test_raises_capability_error(self, backend_name, rounding, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        expr = ma.col("ts").dt.round_temporal(rounding=rounding, unit="HOUR")
        with pytest.raises(BackendCapabilityError) as raised:
            collect_expr(df, expr)
        assert raised.value.function_key is FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL


WEEK_CAPABLE_BACKENDS = [
    b for b in TEMPORAL_BACKENDS if b not in ("narwhals-polars", "narwhals-pandas")
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestRoundCalendarFloorCeilDay:
    """DAY is supported on every backend."""

    def test_floor_day(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_calendar(rounding="FLOOR", unit="DAY")
        )
        assert actual == [datetime(2026, 3, 15, 0, 0, 0)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", WEEK_CAPABLE_BACKENDS)
class TestRoundCalendarFloorCeilWeek:
    """narwhals dt.truncate rejects the '1w' duration on both dialects."""

    def test_floor_week(self, backend_name, backend_factory, collect_expr):
        # 2026-03-15 is a Sunday; ISO week starts Monday 2026-03-09.
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_calendar(rounding="FLOOR", unit="WEEK")
        )
        assert actual == [datetime(2026, 3, 9, 0, 0, 0)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["narwhals-polars", "narwhals-pandas"])
class TestRoundCalendarNarwhalsWeekUnsupported:
    def test_raises_capability_error(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        expr = ma.col("ts").dt.round_calendar(rounding="FLOOR", unit="WEEK")
        with pytest.raises(BackendCapabilityError) as raised:
            collect_expr(df, expr)
        assert raised.value.function_key is FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR

@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", MONTH_YEAR_CAPABLE_BACKENDS)
class TestRoundCalendarFloorCeilMonthYear:
    def test_floor_month(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_calendar(rounding="FLOOR", unit="MONTH")
        )
        assert actual == [datetime(2026, 3, 1, 0, 0, 0)]

    def test_ceil_month(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_calendar(rounding="CEIL", unit="MONTH")
        )
        assert actual == [datetime(2026, 4, 1, 0, 0, 0)]

    def test_floor_year(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_calendar(rounding="FLOOR", unit="YEAR")
        )
        assert actual == [datetime(2026, 1, 1, 0, 0, 0)]

    def test_ceil_year(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_TIE_DATA, backend_name)
        actual = collect_expr(
            df, ma.col("ts").dt.round_calendar(rounding="CEIL", unit="YEAR")
        )
        assert actual == [datetime(2027, 1, 1, 0, 0, 0)]


@pytest.mark.cross_backend
@pytest.mark.parametrize(
    ("unit", "expected"),
    [
        ("MONTH", datetime(2026, 3, 1, 0, 0, 0)),
        ("YEAR", datetime(2026, 1, 1, 0, 0, 0)),
    ],
)
class TestRoundCalendarPolarsMonthYearFloor:
    def test_floor_has_native_value_oracle(
        self, unit, expected, backend_factory, collect_expr
    ):
        df = backend_factory.create(_TIE_DATA, "ibis-polars")
        actual = collect_expr(
            df, ma.col("ts").dt.round_calendar(rounding="FLOOR", unit=unit)
        )
        assert actual == [expected]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", QUARTER_MULTIPLE_CAPABLE_BACKENDS)
class TestRoundCalendarMultiple:
    def test_floor_quarter_via_month_multiple_three(
        self, backend_name, backend_factory, collect_expr
    ):
        df = backend_factory.create(_MULTI_DATA, backend_name)
        actual = collect_expr(
            df,
            ma.col("ts").dt.round_calendar(rounding="FLOOR", unit="MONTH", multiple=3),
        )
        assert actual == [datetime(2026, 1, 1, 0, 0, 0)]

    def test_ceil_quarter_via_month_multiple_three(
        self, backend_name, backend_factory, collect_expr
    ):
        df = backend_factory.create(_MULTI_DATA, backend_name)
        actual = collect_expr(
            df,
            ma.col("ts").dt.round_calendar(rounding="CEIL", unit="MONTH", multiple=3),
        )
        assert actual == [datetime(2026, 4, 1, 0, 0, 0)]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["ibis-sqlite"])
class TestRoundCalendarSqliteMultipleUnsupported:
    def test_raises_capability_error(self, backend_name, backend_factory, collect_expr):
        df = backend_factory.create(_MULTI_DATA, backend_name)
        expr = ma.col("ts").dt.round_calendar(rounding="FLOOR", unit="MONTH", multiple=3)
        with pytest.raises(BackendCapabilityError) as raised:
            collect_expr(df, expr)
        assert raised.value.function_key is FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ["ibis-sqlite"])
class TestMaMultiplierIbisSqliteUnsupported:
    """Ibis SQLite refuses multi-unit MA datetime wrappers natively.

    Single-unit wrappers retain their public values; the multi-unit calls
    dispatch to the exact temporal or calendar rounding implementation that
    cannot lower them.
    """

    @pytest.mark.parametrize(
        ("op", "unit", "function_key"),
        [
            ("truncate", "2d", FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL),
            ("round", "3h", FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL),
            ("ceil", "12mo", FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR),
            ("floor", "2w", FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR),
        ],
    )
    def test_multiplier_unit_raises_capability_error(
        self, backend_name, op, unit, function_key, backend_factory, collect_expr
    ):
        df = backend_factory.create(_MULTI_DATA, backend_name)
        expr = getattr(ma.col("ts").dt, op)(unit)
        with pytest.raises(BackendCapabilityError) as raised:
            collect_expr(df, expr)
        assert raised.value.function_key is function_key

    @pytest.mark.parametrize(
        ("op", "expected"),
        [
            ("truncate", datetime(2026, 3, 15, 0, 0, 0)),
            ("round", datetime(2026, 3, 15, 0, 0, 0)),
            ("ceil", datetime(2026, 3, 16, 0, 0, 0)),
            ("floor", datetime(2026, 3, 15, 0, 0, 0)),
        ],
    )
    def test_single_unit_has_native_value(
        self, backend_name, op, expected, backend_factory, collect_expr
    ):
        df = backend_factory.create(_MULTI_DATA, backend_name)
        actual = collect_expr(df, getattr(ma.col("ts").dt, op)("1d"))
        assert actual == [expected]
