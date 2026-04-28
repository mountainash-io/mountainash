"""Tests for duration constructor and arithmetic."""
from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl
import pytest

import mountainash as ma


class TestDurationConstructor:
    def test_basic_construction(self):
        """ma.duration() creates a timedelta-backed literal."""
        expr = ma.duration(hours=4)
        node = expr._node
        assert node.value == timedelta(hours=4)

    def test_combined_units(self):
        """Multiple units combine correctly."""
        expr = ma.duration(days=1, hours=2, minutes=30)
        node = expr._node
        assert node.value == timedelta(days=1, hours=2, minutes=30)

    def test_keyword_only(self):
        """duration() rejects positional arguments."""
        with pytest.raises(TypeError):
            ma.duration(1)

    def test_sub_second_precision(self):
        """Millisecond and microsecond precision preserved."""
        expr = ma.duration(milliseconds=500)
        assert expr._node.value == timedelta(milliseconds=500)

        expr2 = ma.duration(microseconds=1500)
        assert expr2._node.value == timedelta(microseconds=1500)


class TestDurationArithmetic:
    @pytest.fixture
    def ts_df(self):
        return pl.DataFrame({
            "ts": [datetime(2026, 1, 1, 12, 0, 0)],
        })

    def test_add_duration(self, ts_df):
        """col + ma.duration() offsets the timestamp."""
        expr = ma.col("ts") + ma.duration(days=7)
        result = ts_df.with_columns(expr.compile(ts_df).alias("offset"))
        assert result["offset"][0] == datetime(2026, 1, 8, 12, 0, 0)

    def test_subtract_duration(self, ts_df):
        """col - ma.duration() offsets the timestamp backwards."""
        expr = ma.col("ts") - ma.duration(hours=1)
        result = ts_df.with_columns(expr.compile(ts_df).alias("offset"))
        assert result["offset"][0] == datetime(2026, 1, 1, 11, 0, 0)

    def test_sub_second_arithmetic(self, ts_df):
        """Sub-second duration arithmetic preserves precision."""
        expr = ma.col("ts") + ma.duration(milliseconds=500)
        result = ts_df.with_columns(expr.compile(ts_df).alias("offset"))
        expected = datetime(2026, 1, 1, 12, 0, 0, 500_000)
        assert result["offset"][0] == expected

    def test_microsecond_arithmetic(self, ts_df):
        """Microsecond duration arithmetic preserves precision."""
        expr = ma.col("ts") + ma.duration(microseconds=1500)
        result = ts_df.with_columns(expr.compile(ts_df).alias("offset"))
        expected = datetime(2026, 1, 1, 12, 0, 0, 1500)
        assert result["offset"][0] == expected


class TestDurationComparison:
    def test_duration_gt(self):
        """Duration comparison works on Polars."""
        df = pl.DataFrame({
            "gap": [timedelta(hours=1), timedelta(hours=5), timedelta(hours=10)],
        })
        expr = ma.col("gap") > ma.duration(hours=4)
        result = df.with_columns(expr.compile(df).alias("long_gap"))
        assert result["long_gap"].to_list() == [False, True, True]


class TestDurationExtraction:
    @pytest.fixture
    def duration_df(self):
        return pl.DataFrame({
            "gap": [
                timedelta(hours=1, minutes=30),
                timedelta(hours=2, seconds=45),
                timedelta(days=1, hours=12),
            ],
        })

    def test_total_seconds(self, duration_df):
        expr = ma.col("gap").dt.total_seconds()
        result = duration_df.with_columns(expr.compile(duration_df).alias("secs"))
        assert result["secs"].to_list() == [5400, 7245, 129600]

    def test_total_minutes(self, duration_df):
        expr = ma.col("gap").dt.total_minutes()
        result = duration_df.with_columns(expr.compile(duration_df).alias("mins"))
        assert result["mins"].to_list() == [90, 120, 2160]

    def test_total_milliseconds(self, duration_df):
        expr = ma.col("gap").dt.total_milliseconds()
        result = duration_df.with_columns(expr.compile(duration_df).alias("ms"))
        assert result["ms"].to_list() == [5400000, 7245000, 129600000]

    def test_total_microseconds(self, duration_df):
        expr = ma.col("gap").dt.total_microseconds()
        result = duration_df.with_columns(expr.compile(duration_df).alias("us"))
        assert result["us"].to_list() == [5400000000, 7245000000, 129600000000]
