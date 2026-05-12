"""Tests for duration constructor, arithmetic, comparison, and extraction."""
from __future__ import annotations

from datetime import datetime, timedelta

import polars as pl
import pytest

import mountainash as ma

DURATION_BACKENDS = [
    "polars",
    "narwhals-polars",
    "ibis-duckdb",
]

DURATION_COMPARISON_BACKENDS = [
    "polars",
    "narwhals-polars",
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
        strict=True,
        reason="Ibis IntervalValue does not support comparison operators (known-divergences.md)",
    )),
]

DURATION_EXTRACTION_BACKENDS = [
    "polars",
    "narwhals-polars",
    pytest.param("ibis-duckdb", marks=pytest.mark.xfail(
        strict=True,
        reason="Ibis IntervalValue has no total_*() methods (known-divergences.md)",
    )),
]


class TestDurationConstructor:
    """Constructor tests are backend-agnostic — they test the AST, not compilation."""

    def test_basic_construction(self):
        expr = ma.duration(hours=4)
        node = expr._node
        assert node.value == timedelta(hours=4)

    def test_combined_units(self):
        expr = ma.duration(days=1, hours=2, minutes=30)
        node = expr._node
        assert node.value == timedelta(days=1, hours=2, minutes=30)

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            ma.duration(1)

    def test_sub_second_precision(self):
        expr = ma.duration(milliseconds=500)
        assert expr._node.value == timedelta(milliseconds=500)

        expr2 = ma.duration(microseconds=1500)
        assert expr2._node.value == timedelta(microseconds=1500)


@pytest.mark.parametrize("backend_name", DURATION_BACKENDS)
class TestDurationArithmetic:
    def test_add_duration(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2026, 1, 1, 12, 0, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts") + ma.duration(days=7)
        result = collect_expr(df, expr)
        assert result == [datetime(2026, 1, 8, 12, 0, 0)]

    def test_subtract_duration(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2026, 1, 1, 12, 0, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts") - ma.duration(hours=1)
        result = collect_expr(df, expr)
        assert result == [datetime(2026, 1, 1, 11, 0, 0)]

    def test_sub_second_arithmetic(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2026, 1, 1, 12, 0, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts") + ma.duration(milliseconds=500)
        result = collect_expr(df, expr)
        assert result == [datetime(2026, 1, 1, 12, 0, 0, 500_000)]

    def test_microsecond_arithmetic(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2026, 1, 1, 12, 0, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts") + ma.duration(microseconds=1500)
        result = collect_expr(df, expr)
        assert result == [datetime(2026, 1, 1, 12, 0, 0, 1500)]


@pytest.mark.parametrize("backend_name", DURATION_COMPARISON_BACKENDS)
class TestDurationComparison:
    def test_duration_gt(self, backend_name, backend_factory, collect_expr):
        data = {"gap": [timedelta(hours=1), timedelta(hours=5), timedelta(hours=10)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("gap") > ma.duration(hours=4)
        result = collect_expr(df, expr)
        assert result == [False, True, True]


@pytest.mark.parametrize("backend_name", DURATION_EXTRACTION_BACKENDS)
class TestDurationExtraction:
    def test_total_seconds(self, backend_name, backend_factory, collect_expr):
        data = {"gap": [timedelta(hours=1, minutes=30), timedelta(hours=2, seconds=45), timedelta(days=1, hours=12)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("gap").dt.total_seconds()
        result = collect_expr(df, expr)
        assert result == [5400, 7245, 129600]

    def test_total_minutes(self, backend_name, backend_factory, collect_expr):
        data = {"gap": [timedelta(hours=1, minutes=30), timedelta(hours=2, seconds=45), timedelta(days=1, hours=12)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("gap").dt.total_minutes()
        result = collect_expr(df, expr)
        assert result == [90, 120, 2160]

    def test_total_milliseconds(self, backend_name, backend_factory, collect_expr):
        data = {"gap": [timedelta(hours=1, minutes=30), timedelta(hours=2, seconds=45), timedelta(days=1, hours=12)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("gap").dt.total_milliseconds()
        result = collect_expr(df, expr)
        assert result == [5400000, 7245000, 129600000]

    def test_total_microseconds(self, backend_name, backend_factory, collect_expr):
        data = {"gap": [timedelta(hours=1, minutes=30), timedelta(hours=2, seconds=45), timedelta(days=1, hours=12)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("gap").dt.total_microseconds()
        result = collect_expr(df, expr)
        assert result == [5400000000, 7245000000, 129600000000]


@pytest.mark.parametrize("backend_name", DURATION_EXTRACTION_BACKENDS)
class TestDurationExtractionNew:
    def test_total_days(self, backend_name, backend_factory, collect_expr):
        data = {"gap": [timedelta(days=3, hours=12), timedelta(days=1), timedelta(hours=36)]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("gap").dt.total_days())
        assert result == [3, 1, 1]

    def test_total_hours(self, backend_name, backend_factory, collect_expr):
        data = {"gap": [timedelta(hours=1, minutes=30), timedelta(hours=25), timedelta(minutes=45)]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("gap").dt.total_hours())
        assert result == [1, 25, 0]


DURATION_POLARS_AND_NARWHALS = [
    "polars",
    "narwhals-polars",
    pytest.param(
        "ibis-duckdb",
        marks=pytest.mark.xfail(strict=True, reason="Ibis IntervalValue has no total_nanoseconds()"),
    ),
]


@pytest.mark.parametrize("backend_name", DURATION_POLARS_AND_NARWHALS)
class TestTotalNanoseconds:
    def test_total_nanoseconds(self, backend_name, backend_factory, collect_expr):
        data = {"gap": [timedelta(seconds=1), timedelta(milliseconds=500)]}
        df = backend_factory.create(data, backend_name)
        result = collect_expr(df, ma.col("gap").dt.total_nanoseconds())
        assert result == [1_000_000_000, 500_000_000]
