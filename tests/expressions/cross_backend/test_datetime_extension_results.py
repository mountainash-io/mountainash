"""Cross-backend result verification for datetime/duration operations.

Verifies that duration total_* expressions produce identical results across
backends with temporal support. Ibis backends are excluded because
IntervalValue lacks total_* methods (they use diff_* instead).

Also verifies timestamp component extraction (microsecond, nanosecond)
and timezone operations (assume_timezone) across all backends.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from mountainash.core.capabilities import load_all_capability_declarations
from fixtures.capability_gating import xfail_divergence
import mountainash as ma

# Load capability declarations at import (house convention: mirror
# test_datetime_value_class_dispatch / test_option_fact_integrity). The
# assume_timezone disposition below asserts the capability gate RAISES on the
# ibis/narwhals backends; without this the gate is inert under standalone
# collection and the raise-assertions would spuriously fail. The full CI suite
# loads declarations globally, so this makes the gate state deterministic here.
load_all_capability_declarations()


DURATION_BACKENDS = [
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
]


# =============================================================================
# total_seconds
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", DURATION_BACKENDS)
class TestDtTotalSeconds:
    def test_total_seconds_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "dur": [
                timedelta(hours=1, minutes=30, seconds=15),
                timedelta(days=1),
                timedelta(seconds=90),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_seconds())
        assert actual == [5415, 86400, 90]

    def test_total_seconds_zero(self, backend_name, backend_factory, collect_expr):
        data = {"dur": [timedelta(0), timedelta(seconds=1)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_seconds())
        assert actual == [0, 1]


# =============================================================================
# total_minutes
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", DURATION_BACKENDS)
class TestDtTotalMinutes:
    def test_total_minutes_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "dur": [
                timedelta(hours=1, minutes=30, seconds=15),
                timedelta(days=1),
                timedelta(seconds=90),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_minutes())
        # Truncated integer: 1h30m15s = 90 minutes (not 90.25)
        assert actual == [90, 1440, 1]

    def test_total_minutes_zero(self, backend_name, backend_factory, collect_expr):
        data = {"dur": [timedelta(0), timedelta(minutes=5)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_minutes())
        assert actual == [0, 5]


# =============================================================================
# total_hours
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", DURATION_BACKENDS)
class TestDtTotalHours:
    def test_total_hours_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "dur": [
                timedelta(hours=1, minutes=30, seconds=15),
                timedelta(days=1),
                timedelta(seconds=90),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_hours())
        # Truncated integer: 1h30m15s = 1 hour
        assert actual == [1, 24, 0]

    def test_total_hours_zero(self, backend_name, backend_factory, collect_expr):
        data = {"dur": [timedelta(0), timedelta(hours=3)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_hours())
        assert actual == [0, 3]


# =============================================================================
# total_days
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", DURATION_BACKENDS)
class TestDtTotalDays:
    def test_total_days_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "dur": [
                timedelta(hours=1, minutes=30, seconds=15),
                timedelta(days=1),
                timedelta(days=3, hours=12),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_days())
        # Truncated integer: 3d12h = 3 days
        assert actual == [0, 1, 3]

    def test_total_days_zero(self, backend_name, backend_factory, collect_expr):
        data = {"dur": [timedelta(0), timedelta(days=7)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_days())
        assert actual == [0, 7]


# =============================================================================
# total_milliseconds
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", DURATION_BACKENDS)
class TestDtTotalMilliseconds:
    def test_total_milliseconds_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "dur": [
                timedelta(hours=1, minutes=30, seconds=15),
                timedelta(days=1),
                timedelta(seconds=90),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_milliseconds())
        assert actual == [5415000, 86400000, 90000]

    def test_total_milliseconds_zero(self, backend_name, backend_factory, collect_expr):
        data = {"dur": [timedelta(0), timedelta(milliseconds=500)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_milliseconds())
        assert actual == [0, 500]


# =============================================================================
# total_microseconds
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", DURATION_BACKENDS)
class TestDtTotalMicroseconds:
    def test_total_microseconds_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "dur": [
                timedelta(hours=1, minutes=30, seconds=15),
                timedelta(days=1),
                timedelta(seconds=90),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_microseconds())
        assert actual == [5415000000, 86400000000, 90000000]

    def test_total_microseconds_zero(self, backend_name, backend_factory, collect_expr):
        data = {"dur": [timedelta(0), timedelta(microseconds=750)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_microseconds())
        assert actual == [0, 750]


# =============================================================================
# total_nanoseconds
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", DURATION_BACKENDS)
class TestDtTotalNanoseconds:
    def test_total_nanoseconds_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "dur": [
                timedelta(hours=1, minutes=30, seconds=15),
                timedelta(days=1),
                timedelta(seconds=90),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_nanoseconds())
        assert actual == [5415000000000, 86400000000000, 90000000000]

    def test_total_nanoseconds_zero(self, backend_name, backend_factory, collect_expr):
        data = {"dur": [timedelta(0), timedelta(seconds=1)]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("dur").dt.total_nanoseconds())
        assert actual == [0, 1000000000]


# =============================================================================
# Timestamp component extraction and timezone operations
# =============================================================================

TIMESTAMP_BACKENDS = [
    "polars",
    "polars-lazy",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
]

_MICRO_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("IB-DT-15", backend=b)) for b in TIMESTAMP_BACKENDS
]
_NANO_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("IB-DT-16", backend=b)) for b in TIMESTAMP_BACKENDS
]


# =============================================================================
# microsecond
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _MICRO_BACKENDS)
class TestDtMicrosecond:
    def test_microsecond_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 3, 15, 10, 30, 45, 123456),
                datetime(2024, 6, 20, 14, 0, 0, 500000),
                datetime(2024, 12, 31, 23, 59, 59, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.microsecond())
        assert actual == [123456, 500000, 0]

    def test_microsecond_zero(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 1, 1, 0, 0, 0, 0),
                datetime(2024, 1, 1, 0, 0, 0, 1),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.microsecond())
        assert actual == [0, 1]


# =============================================================================
# nanosecond
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _NANO_BACKENDS)
class TestDtNanosecond:
    def test_nanosecond_basic(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 3, 15, 10, 30, 45, 123456),
                datetime(2024, 6, 20, 14, 0, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.nanosecond())
        # Python datetime has microsecond precision; nanosecond = microsecond * 1000
        assert actual == [123456000, 0]

    def test_nanosecond_zero(self, backend_name, backend_factory, collect_expr):
        data = {
            "ts": [
                datetime(2024, 1, 1, 0, 0, 0, 0),
                datetime(2024, 1, 1, 0, 0, 0, 500000),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.nanosecond())
        assert actual == [0, 500000000]

