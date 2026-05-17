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
