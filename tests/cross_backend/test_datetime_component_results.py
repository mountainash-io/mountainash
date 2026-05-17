"""Cross-backend result verification for datetime component extraction.

Verifies that datetime component extraction produces identical results
across all temporal backends.
"""

from __future__ import annotations

from datetime import datetime

import pytest

import mountainash as ma

TEMPORAL_BACKENDS = [
    "polars",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtYear:
    def test_year_basic(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15, 10, 30, 45), datetime(2023, 12, 25, 0, 0, 0)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.year())
        assert actual == [2024, 2023]

    def test_year_boundary(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2000, 1, 1), datetime(1999, 12, 31)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.year())
        assert actual == [2000, 1999]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtMonth:
    def test_month_basic(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15), datetime(2024, 12, 25), datetime(2024, 1, 1)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.month())
        assert actual == [3, 12, 1]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtDay:
    def test_day_basic(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15), datetime(2024, 12, 25), datetime(2024, 1, 31)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.day())
        assert actual == [15, 25, 31]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtHour:
    def test_hour_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 1, 23, 0, 0),
                datetime(2024, 1, 1, 0, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.hour())
        assert actual == [10, 23, 0]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtMinute:
    def test_minute_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 1, 1, 10, 30, 0),
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 1, 10, 59, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.minute())
        assert actual == [30, 0, 59]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtSecond:
    def test_second_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 1, 1, 10, 30, 45),
                datetime(2024, 1, 1, 10, 30, 0),
                datetime(2024, 1, 1, 10, 30, 59),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.second())
        assert actual == [45, 0, 59]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtWeekday:
    def test_weekday_basic(self, backend_name, backend_factory, collect_expr):
        # 2024-03-15 = Friday, 2024-03-18 = Monday
        data = {"ts": [datetime(2024, 3, 15), datetime(2024, 3, 18)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.weekday())
        # Friday: Polars=5 (Mon=1), Python=4 (Mon=0), ISO=5
        # Monday: Polars=1, Python=0, ISO=1
        assert actual[0] in [4, 5, 6]  # Friday
        assert actual[1] in [0, 1]  # Monday


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtOrdinalDay:
    def test_ordinal_day_basic(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 1, 1), datetime(2024, 3, 15), datetime(2024, 12, 31)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.ordinal_day())
        assert actual == [1, 75, 366]  # 2024 is leap year


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtQuarter:
    def test_quarter_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 1, 15),
                datetime(2024, 4, 15),
                datetime(2024, 7, 15),
                datetime(2024, 10, 15),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.quarter())
        assert actual == [1, 2, 3, 4]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtIsLeapYear:
    def test_is_leap_year_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 6, 1),
                datetime(2023, 6, 1),
                datetime(2000, 6, 1),
                datetime(1900, 6, 1),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.is_leap_year())
        assert actual == [True, False, True, False]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtDate:
    def test_date_extraction(self, backend_name, backend_factory, collect_expr):
        from datetime import date

        if backend_name in ("narwhals-pandas", "ibis-duckdb", "ibis-polars", "ibis-sqlite"):
            pytest.xfail(
                f"{backend_name}: dt.date() returns datetime with zeroed time instead of date"
            )

        data = {"ts": [datetime(2024, 3, 15, 10, 30, 45), datetime(2024, 12, 25, 23, 59, 0)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.date())
        expected = [date(2024, 3, 15), date(2024, 12, 25)]
        assert actual == expected


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TEMPORAL_BACKENDS)
class TestDtTime:
    def test_time_extraction(self, backend_name, backend_factory, collect_expr):
        from datetime import time

        if backend_name in ("narwhals-polars", "narwhals-pandas"):
            pytest.xfail(f"{backend_name}: Narwhals does not support dt.time()")
        if backend_name == "ibis-sqlite":
            pytest.xfail("ibis-sqlite: dt.time() returns timedelta instead of time")

        data = {"ts": [datetime(2024, 3, 15, 10, 30, 45), datetime(2024, 12, 25, 23, 59, 0)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.time())
        expected = [time(10, 30, 45), time(23, 59, 0)]
        assert actual == expected
