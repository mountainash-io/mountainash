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

import mountainash as ma


DURATION_BACKENDS = [
    "polars",
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
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite",
]


# =============================================================================
# microsecond
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TIMESTAMP_BACKENDS)
class TestDtMicrosecond:
    def test_microsecond_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "ibis-sqlite returns seconds instead of microseconds for "
                "microsecond extraction"
            )
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
        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "ibis-sqlite returns seconds instead of microseconds for "
                "microsecond extraction"
            )
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
@pytest.mark.parametrize("backend_name", TIMESTAMP_BACKENDS)
class TestDtNanosecond:
    def test_nanosecond_basic(self, backend_name, backend_factory, collect_expr):
        if backend_name in ("ibis-duckdb", "ibis-polars", "ibis-sqlite"):
            pytest.xfail(
                f"{backend_name} returns 0 for nanosecond — no sub-microsecond "
                "precision from Python datetime inputs"
            )
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
        if backend_name in ("ibis-duckdb", "ibis-polars", "ibis-sqlite"):
            pytest.xfail(
                f"{backend_name} returns 0 for nanosecond — no sub-microsecond "
                "precision from Python datetime inputs"
            )
        data = {
            "ts": [
                datetime(2024, 1, 1, 0, 0, 0, 0),
                datetime(2024, 1, 1, 0, 0, 0, 500000),
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("ts").dt.nanosecond())
        assert actual == [0, 500000000]


# =============================================================================
# assume_timezone
# =============================================================================


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", TIMESTAMP_BACKENDS)
class TestDtAssumeTimezone:
    def test_assume_timezone_preserves_hour(
        self, backend_name, backend_factory, collect_expr
    ):
        """Assume UTC then extract hour — should be the same hour as the naive input."""
        data = {
            "ts": [
                datetime(2024, 3, 15, 10, 30, 0),
                datetime(2024, 6, 20, 14, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.assume_timezone("UTC").dt.hour()
        actual = collect_expr(df, expr)
        assert actual == [10, 14]

    def test_assume_timezone_runs_without_error(
        self, backend_name, backend_factory
    ):
        """Smoke test: assume_timezone should not raise."""
        data = {
            "ts": [
                datetime(2024, 3, 15, 10, 30, 0),
                datetime(2024, 6, 20, 14, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)
        result = (
            ma.relation(df)
            .select(ma.col("ts").dt.assume_timezone("UTC").name.alias("tz_ts"))
            .to_dict()
        )
        assert len(result["tz_ts"]) == 2
