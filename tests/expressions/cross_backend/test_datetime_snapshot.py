"""Cross-backend tests for today() and now() snapshot functions."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
import mountainash as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTodaySnapshot:
    def test_today_returns_current_date(self, backend_name, backend_factory):
        if backend_name.startswith("ibis"):
            pytest.xfail(
                "Ibis today() returns datetime(date, 0:00) not date — "
                "ibis.literal(date.today()) upcasts to timestamp"
            )
        df = backend_factory.create({"a": [1, 2, 3]}, backend_name)
        result = ma.relation(df).with_columns(
            ma.today().name.alias("d")
        ).to_polars()
        assert result["d"][0] in (date.today(), date.today() - timedelta(days=1))

    def test_today_free_function_matches_fluent(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1]}, backend_name)
        free = ma.relation(df).with_columns(
            ma.today().name.alias("d")
        ).to_polars()["d"][0]
        fluent = ma.relation(df).with_columns(
            ma.col("a").dt.today().name.alias("d")
        ).to_polars()["d"][0]
        assert free == fluent


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNowSnapshot:
    def test_now_returns_recent_datetime(self, backend_name, backend_factory):
        if backend_name in ("ibis-duckdb", "ibis-sqlite"):
            pytest.xfail(
                "Ibis now() uses CURRENT_TIMESTAMP (UTC) on SQL backends — "
                "diverges from Python datetime.now() (local time)"
            )
        before = datetime.now()
        df = backend_factory.create({"a": [1, 2, 3]}, backend_name)
        result = ma.relation(df).with_columns(
            ma.now().name.alias("ts")
        ).to_polars()
        after = datetime.now()
        ts = result["ts"][0]
        assert before - timedelta(seconds=5) <= ts <= after + timedelta(seconds=5)

    def test_now_free_function_matches_fluent(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1]}, backend_name)
        free = ma.relation(df).with_columns(
            ma.now().name.alias("ts")
        ).to_polars()["ts"][0]
        fluent = ma.relation(df).with_columns(
            ma.col("a").dt.now().name.alias("ts")
        ).to_polars()["ts"][0]
        assert abs((free - fluent).total_seconds()) < 2
