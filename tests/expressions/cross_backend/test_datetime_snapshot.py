"""Cross-backend tests for today() and now() snapshot functions."""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta

import pytest
import mountainash as ma

from fixtures.backend_registry import ALL_BACKENDS


# A fixed non-UTC clock makes IB-DT-09 observable even on UTC CI runners.
# Backend applicability and strict expected failures come from the declaration.


@pytest.fixture
def non_utc_timezone(monkeypatch):
    try:
        with monkeypatch.context() as environment:
            # POSIX fixed offset: UTC-5, with no DST or timezone database lookup.
            environment.setenv("TZ", "EST5")
            time.tzset()
            yield
    finally:
        time.tzset()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTodaySnapshot:
    def test_today_returns_current_date(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1, 2, 3]}, backend_name)
        result = ma.relation(df).with_columns(ma.today().name.alias("d")).to_polars()
        assert result["d"][0] in (date.today(), date.today() - timedelta(days=1))


@pytest.mark.parametrize("backend_name", ["ibis-duckdb", "ibis-polars", "ibis-sqlite"])
def test_today_compiles_to_native_date_on_ibis(backend_name, backend_factory):
    df = backend_factory.create({"a": [1]}, backend_name)
    assert ma.today().compile(df).type().is_date()


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestNowSnapshot:
    def test_now_returns_recent_datetime(self, backend_name, backend_factory, non_utc_timezone):
        before = datetime.now()
        df = backend_factory.create({"a": [1, 2, 3]}, backend_name)
        result = ma.relation(df).with_columns(ma.now().name.alias("ts")).to_polars()
        after = datetime.now()
        ts = result["ts"][0]
        assert before - timedelta(seconds=5) <= ts <= after + timedelta(seconds=5)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSnapshotFreeFunctionMatchesFluent:
    """Free-function and fluent snapshots agree on every backend."""

    def test_today_free_function_matches_fluent(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1]}, backend_name)
        free = ma.relation(df).with_columns(ma.today().name.alias("d")).to_polars()["d"][0]
        fluent = ma.relation(df).with_columns(ma.col("a").dt.today().name.alias("d")).to_polars()["d"][0]
        assert free == fluent

    def test_now_free_function_matches_fluent(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1]}, backend_name)
        free = ma.relation(df).with_columns(ma.now().name.alias("ts")).to_polars()["ts"][0]
        fluent = ma.relation(df).with_columns(ma.col("a").dt.now().name.alias("ts")).to_polars()["ts"][0]
        assert abs((free - fluent).total_seconds()) < 2
