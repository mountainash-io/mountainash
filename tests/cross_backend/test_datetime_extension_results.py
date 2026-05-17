"""Cross-backend result verification for datetime/duration operations.

Verifies that duration total_* expressions produce identical results across
backends with temporal support. Ibis backends are excluded because
IntervalValue lacks total_* methods (they use diff_* instead).
"""

from __future__ import annotations

from datetime import timedelta

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
