"""Cross-backend tests for extended datetime operations coverage."""

import pytest
from datetime import datetime
import mountainash_expressions as ma


ALL_BACKENDS = [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeCalendar:
    """Test calendar extraction: quarter, day_of_year, day_of_week, week_of_year, iso_year."""

    def test_quarter(self, backend_name, backend_factory, select_and_extract):
        """Test quarter extraction."""
        data = {"ts": [datetime(2024, 1, 15), datetime(2024, 4, 15), datetime(2024, 7, 15), datetime(2024, 10, 15)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.quarter()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [1, 2, 3, 4], f"[{backend_name}] got {actual}"

    def test_day_of_year(self, backend_name, backend_factory, select_and_extract):
        """Test day_of_year extraction."""
        data = {"ts": [datetime(2024, 1, 1), datetime(2024, 2, 1), datetime(2024, 12, 31)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.day_of_year()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] == 1, f"[{backend_name}] Jan 1 should be day 1: {actual[0]}"
        assert actual[1] == 32, f"[{backend_name}] Feb 1 should be day 32: {actual[1]}"
        assert actual[2] == 366, f"[{backend_name}] Dec 31 2024 (leap) should be day 366: {actual[2]}"

    def test_week_of_year(self, backend_name, backend_factory, select_and_extract):
        """Test week_of_year extraction."""
        if backend_name in ("pandas", "narwhals"):
            pytest.xfail(f"{backend_name}: week_of_year not supported.")
        data = {"ts": [datetime(2024, 1, 1), datetime(2024, 1, 7), datetime(2024, 6, 15)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.week_of_year()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] >= 1, f"[{backend_name}] Jan 1 week should be >= 1: {actual[0]}"

    def test_iso_year(self, backend_name, backend_factory, select_and_extract):
        """Test iso_year extraction."""
        data = {"ts": [datetime(2024, 6, 15), datetime(2025, 1, 1)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.iso_year()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] == 2024, f"[{backend_name}] Mid-2024 iso_year: {actual[0]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeSpecial:
    """Test special extraction: unix_timestamp, is_leap_year."""

    def test_unix_timestamp(self, backend_name, backend_factory, select_and_extract):
        """Test unix_timestamp extraction."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type.")
        data = {"ts": [datetime(2024, 1, 1), datetime(2024, 7, 1)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.unix_timestamp()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] > 0, f"[{backend_name}] Expected positive epoch: {actual[0]}"
        assert actual[0] < actual[1], f"[{backend_name}] Jan should be before Jul: {actual}"

    def test_is_leap_year(self, backend_name, backend_factory, select_and_extract):
        """Test is_leap_year boolean extraction."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type.")
        data = {"ts": [datetime(2024, 6, 1), datetime(2023, 6, 1)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.is_leap_year()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] is True, f"[{backend_name}] 2024 is a leap year: {actual[0]}"
        assert actual[1] is False, f"[{backend_name}] 2023 is not a leap year: {actual[1]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeArithmetic:
    """Test calendar arithmetic: add_years, add_months."""

    def test_add_years(self, backend_name, backend_factory, select_and_extract):
        """Test add_years."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type. Calendar intervals not supported.")
        if backend_name == "ibis-polars":
            pytest.xfail("Ibis Polars backend doesn't support calendar-based intervals.")
        data = {"ts": [datetime(2024, 1, 15), datetime(2024, 6, 15)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.add_years(1).dt.year()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [2025, 2025], f"[{backend_name}] got {actual}"

    def test_add_months(self, backend_name, backend_factory, select_and_extract):
        """Test add_months."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type. Calendar intervals not supported.")
        if backend_name == "ibis-polars":
            pytest.xfail("Ibis Polars backend doesn't support calendar-based intervals.")
        data = {"ts": [datetime(2024, 1, 15), datetime(2024, 10, 15)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.add_months(3).dt.month()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual == [4, 1], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeDiff:
    """Test diff operations: diff_years, diff_days."""

    def test_diff_years(self, backend_name, backend_factory, select_and_extract):
        """Test diff_years between two date columns."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type.")
        data = {
            "start": [datetime(2020, 1, 1), datetime(2022, 6, 1)],
            "end": [datetime(2024, 1, 1), datetime(2024, 6, 1)],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("end").dt.diff_years(ma.col("start"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] == 4, f"[{backend_name}] Expected 4 year diff: {actual[0]}"
        assert actual[1] == 2, f"[{backend_name}] Expected 2 year diff: {actual[1]}"

    def test_diff_days(self, backend_name, backend_factory, select_and_extract):
        """Test diff_days between two date columns."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type.")
        if backend_name in ("pandas", "narwhals"):
            pytest.xfail(f"{backend_name}: diff_days not supported.")
        if backend_name == "ibis-polars":
            pytest.xfail("Ibis Polars: TimestampDelta not supported.")
        data = {
            "start": [datetime(2024, 1, 1), datetime(2024, 3, 1)],
            "end": [datetime(2024, 1, 11), datetime(2024, 3, 31)],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("end").dt.diff_days(ma.col("start"))
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] == 10, f"[{backend_name}] Expected 10 day diff: {actual[0]}"
        assert actual[1] == 30, f"[{backend_name}] Expected 30 day diff: {actual[1]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeFormat:
    """Test formatting: strftime."""

    def test_strftime(self, backend_name, backend_factory, select_and_extract):
        """Test strftime formatting."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type.")
        if backend_name == "narwhals":
            pytest.xfail("Narwhals: strftime not supported.")
        data = {"ts": [datetime(2024, 3, 15), datetime(2024, 12, 25)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.strftime("%Y-%m-%d")
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] == "2024-03-15", f"[{backend_name}] got {actual[0]}"
        assert actual[1] == "2024-12-25", f"[{backend_name}] got {actual[1]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeSubSecond:
    """Test sub-second extraction: millisecond."""

    def test_millisecond(self, backend_name, backend_factory, select_and_extract):
        """Test millisecond extraction."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type.")
        data = {"ts": [datetime(2024, 1, 1, 12, 0, 0, 500000), datetime(2024, 1, 1, 12, 0, 0, 250000)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.millisecond()
        actual = select_and_extract(df, expr.compile(df), "result", backend_name)
        assert actual[0] == 500, f"[{backend_name}] Expected 500ms: {actual[0]}"
        assert actual[1] == 250, f"[{backend_name}] Expected 250ms: {actual[1]}"
