"""Cross-backend tests for extended datetime operations coverage."""

import pytest
from datetime import datetime
import mountainash.expressions as ma
from fixtures.backend_registry import ALL_BACKENDS
from fixtures.capability_gating import xfail_divergence

# week_of_year: pandas + all narwhals lack ISO week (NW-DT-06, bare BCE).
_WEEK_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("NW-DT-06", backend=b)) for b in ALL_BACKENDS
]
# calendar-interval add (add_years/add_months): ibis-polars TypeError (IB-DT-10).
_CALINT_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("IB-DT-10", backend=b)) for b in ALL_BACKENDS
]
# time-unit differences (diff_days): ibis-polars/ibis-sqlite no TimestampDelta (IB-DT-11).
_DIFF_BACKENDS = [
    pytest.param(b, marks=xfail_divergence("IB-DT-11", backend=b)) for b in ALL_BACKENDS
]


@pytest.mark.cross_backend
class TestComposeDatetimeCalendar:
    """Test calendar extraction: quarter, day_of_year, day_of_week, week_of_year, iso_year."""

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_quarter(self, backend_name, backend_factory, collect_expr):
        """Test quarter extraction."""
        data = {"ts": [datetime(2024, 1, 15), datetime(2024, 4, 15), datetime(2024, 7, 15), datetime(2024, 10, 15)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.quarter()
        actual = collect_expr(df, expr)
        assert actual == [1, 2, 3, 4], f"[{backend_name}] got {actual}"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_day_of_year(self, backend_name, backend_factory, collect_expr):
        """Test day_of_year extraction."""
        data = {"ts": [datetime(2024, 1, 1), datetime(2024, 2, 1), datetime(2024, 12, 31)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.day_of_year()
        actual = collect_expr(df, expr)
        assert actual[0] == 1, f"[{backend_name}] Jan 1 should be day 1: {actual[0]}"
        assert actual[1] == 32, f"[{backend_name}] Feb 1 should be day 32: {actual[1]}"
        assert actual[2] == 366, f"[{backend_name}] Dec 31 2024 (leap) should be day 366: {actual[2]}"

    @pytest.mark.parametrize("backend_name", _WEEK_BACKENDS)
    def test_week_of_year(self, backend_name, backend_factory, collect_expr):
        """Test week_of_year extraction."""
        data = {"ts": [datetime(2024, 1, 1), datetime(2024, 1, 7), datetime(2024, 6, 15)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.week_of_year()
        actual = collect_expr(df, expr)
        assert actual[0] >= 1, f"[{backend_name}] Jan 1 week should be >= 1: {actual[0]}"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_iso_year(self, backend_name, backend_factory, collect_expr):
        """Test iso_year extraction."""
        data = {"ts": [datetime(2024, 6, 15), datetime(2025, 1, 1)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.iso_year()
        actual = collect_expr(df, expr)
        assert actual[0] == 2024, f"[{backend_name}] Mid-2024 iso_year: {actual[0]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeSpecial:
    """Test special extraction: unix_timestamp, is_leap_year."""

    def test_unix_timestamp(self, backend_name, backend_factory, collect_expr):
        """Test unix_timestamp extraction."""
        data = {"ts": [datetime(2024, 1, 1), datetime(2024, 7, 1)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.unix_timestamp()
        actual = collect_expr(df, expr)
        assert actual[0] > 0, f"[{backend_name}] Expected positive epoch: {actual[0]}"
        assert actual[0] < actual[1], f"[{backend_name}] Jan should be before Jul: {actual}"

    def test_is_leap_year(self, backend_name, backend_factory, collect_expr):
        """Test is_leap_year boolean extraction."""
        data = {"ts": [datetime(2024, 6, 1), datetime(2023, 6, 1)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.is_leap_year()
        actual = collect_expr(df, expr)
        assert actual[0] is True, f"[{backend_name}] 2024 is a leap year: {actual[0]}"
        assert actual[1] is False, f"[{backend_name}] 2023 is not a leap year: {actual[1]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _CALINT_BACKENDS)
class TestComposeDatetimeArithmetic:
    """Test calendar arithmetic: add_years, add_months."""

    def test_add_years(self, backend_name, backend_factory, collect_expr):
        """Test add_years."""
        data = {"ts": [datetime(2024, 1, 15), datetime(2024, 6, 15)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.add_years(1).dt.year()
        actual = collect_expr(df, expr)
        assert actual == [2025, 2025], f"[{backend_name}] got {actual}"

    def test_add_months(self, backend_name, backend_factory, collect_expr):
        """Test add_months."""
        data = {"ts": [datetime(2024, 1, 15), datetime(2024, 10, 15)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.add_months(3).dt.month()
        actual = collect_expr(df, expr)
        assert actual == [4, 1], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
class TestComposeDatetimeDiff:
    """Test diff operations: diff_years, diff_days."""

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_diff_years(self, backend_name, backend_factory, collect_expr):
        """Test diff_years between two date columns."""
        data = {
            "start": [datetime(2020, 1, 1), datetime(2022, 6, 1)],
            "end": [datetime(2024, 1, 1), datetime(2024, 6, 1)],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("end").dt.diff_years(ma.col("start"))
        actual = collect_expr(df, expr)
        assert actual[0] == 4, f"[{backend_name}] Expected 4 year diff: {actual[0]}"
        assert actual[1] == 2, f"[{backend_name}] Expected 2 year diff: {actual[1]}"

    @pytest.mark.parametrize("backend_name", _DIFF_BACKENDS)
    def test_diff_days(self, backend_name, backend_factory, collect_expr):
        """Test diff_days between two date columns."""
        data = {
            "start": [datetime(2024, 1, 1), datetime(2024, 3, 1)],
            "end": [datetime(2024, 1, 11), datetime(2024, 3, 31)],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("end").dt.diff_days(ma.col("start"))
        actual = collect_expr(df, expr)
        assert actual[0] == 10, f"[{backend_name}] Expected 10 day diff: {actual[0]}"
        assert actual[1] == 30, f"[{backend_name}] Expected 30 day diff: {actual[1]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeFormat:
    """Test formatting: strftime."""

    def test_strftime(self, backend_name, backend_factory, collect_expr):
        """Test strftime formatting."""
        data = {"ts": [datetime(2024, 3, 15), datetime(2024, 12, 25)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.strftime("%Y-%m-%d")
        actual = collect_expr(df, expr)
        assert actual[0] == "2024-03-15", f"[{backend_name}] got {actual[0]}"
        assert actual[1] == "2024-12-25", f"[{backend_name}] got {actual[1]}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestComposeDatetimeSubSecond:
    """Test sub-second extraction: millisecond."""

    def test_millisecond(self, backend_name, backend_factory, collect_expr):
        """Test millisecond extraction."""
        data = {"ts": [datetime(2024, 1, 1, 12, 0, 0, 500000), datetime(2024, 1, 1, 12, 0, 0, 250000)]}
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.millisecond()
        actual = collect_expr(df, expr)
        assert actual[0] == 500, f"[{backend_name}] Expected 500ms: {actual[0]}"
        assert actual[1] == 250, f"[{backend_name}] Expected 250ms: {actual[1]}"
