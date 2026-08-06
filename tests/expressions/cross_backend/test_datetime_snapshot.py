"""Cross-backend tests for today() and now() snapshot functions."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
import mountainash as ma

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence


# now() compiles to query-time UTC SQL on ibis-duckdb/ibis-sqlite (IB-DT-09);
# ibis-polars evaluates now() like Polars/Narwhals, so it is NOT gated here.
# The mark is non-strict: the UTC-vs-local divergence only manifests off UTC, so
# a UTC runner (e.g. CI) legitimately passes — tolerate the xpass rather than
# flake on it.
_NOW_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("IB-DT-09", backend=b, strict=False))
    if b in ("ibis-duckdb", "ibis-sqlite")
    else b
    for b in ALL_BACKENDS
]


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestTodaySnapshot:
    def test_today_returns_current_date(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1, 2, 3]}, backend_name)
        result = ma.relation(df).with_columns(
            ma.today().name.alias("d")
        ).to_polars()
        assert result["d"][0] in (date.today(), date.today() - timedelta(days=1))


@pytest.mark.parametrize("backend_name", _NOW_BACKENDS)
class TestNowSnapshot:
    def test_now_returns_recent_datetime(self, backend_name, backend_factory):
        before = datetime.now()
        df = backend_factory.create({"a": [1, 2, 3]}, backend_name)
        result = ma.relation(df).with_columns(
            ma.now().name.alias("ts")
        ).to_polars()
        after = datetime.now()
        ts = result["ts"][0]
        assert before - timedelta(seconds=5) <= ts <= after + timedelta(seconds=5)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestSnapshotFreeFunctionMatchesFluent:
    """Free-function vs fluent equivalence holds on every backend (both paths
    produce the same value, including the ibis upcast), so no gating is needed."""

    def test_today_free_function_matches_fluent(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1]}, backend_name)
        free = ma.relation(df).with_columns(
            ma.today().name.alias("d")
        ).to_polars()["d"][0]
        fluent = ma.relation(df).with_columns(
            ma.col("a").dt.today().name.alias("d")
        ).to_polars()["d"][0]
        assert free == fluent

    def test_now_free_function_matches_fluent(self, backend_name, backend_factory):
        df = backend_factory.create({"a": [1]}, backend_name)
        free = ma.relation(df).with_columns(
            ma.now().name.alias("ts")
        ).to_polars()["ts"][0]
        fluent = ma.relation(df).with_columns(
            ma.col("a").dt.now().name.alias("ts")
        ).to_polars()["ts"][0]
        assert abs((free - fluent).total_seconds()) < 2
