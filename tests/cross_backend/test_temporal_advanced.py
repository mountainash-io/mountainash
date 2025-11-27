"""
Cross-backend tests for advanced temporal operations.

Tests time arithmetic, intervals, and truncation operations:
- Adding hours, minutes, seconds to datetimes
- Calculating time differences
- DateTime truncation
- Flexible offset operations
- Chaining temporal operations

These tests validate that temporal arithmetic works consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
from datetime import datetime, timedelta
import mountainash_expressions as ma


# =============================================================================
# Cross-Backend Tests - Time Component Addition
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestAddTimeComponents:
    """Test adding hours, minutes, seconds to datetimes."""

    def test_add_hours(self, backend_name, backend_factory, select_and_extract):
        """Test adding hours to datetimes."""
        data = {
            "timestamp": [
                datetime(2024, 1, 1, 10, 30, 45),
                datetime(2024, 1, 1, 14, 15, 30),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Add 2 hours
        expr = ma.col("timestamp").dt.add_hours(2)
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [
            datetime(2024, 1, 1, 12, 30, 45),
            datetime(2024, 1, 1, 16, 15, 30)
        ]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_add_minutes(self, backend_name, backend_factory, select_and_extract):
        """Test adding minutes to datetimes."""
        data = {
            "timestamp": [
                datetime(2024, 1, 1, 10, 30, 45),
                datetime(2024, 1, 1, 14, 15, 30),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Add 30 minutes
        expr = ma.col("timestamp").dt.add_minutes(30)
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [
            datetime(2024, 1, 1, 11, 0, 45),
            datetime(2024, 1, 1, 14, 45, 30)
        ]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_add_seconds(self, backend_name, backend_factory, select_and_extract):
        """Test adding seconds to datetimes."""
        data = {
            "timestamp": [
                datetime(2024, 1, 1, 10, 30, 45),
                datetime(2024, 1, 1, 14, 15, 30),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Add 15 seconds
        expr = ma.col("timestamp").dt.add_seconds(15)
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [
            datetime(2024, 1, 1, 10, 31, 0),
            datetime(2024, 1, 1, 14, 15, 45)
        ]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Time Differences
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestTimeDifferences:
    """Test calculating time differences in various units."""

    def test_diff_hours(self, backend_name, backend_factory, select_and_extract):
        """Test calculating difference in hours between datetimes."""

        data = {
            "start": [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 1, 14, 30, 0),
            ],
            "end": [
                datetime(2024, 1, 1, 13, 0, 0),
                datetime(2024, 1, 1, 16, 45, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Calculate difference in hours
        expr = ma.col("end").dt.diff_hours(ma.col("start"))
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "diff", backend_name)

        # 3 hours, 2.25 hours (rounded to 2 for int representation)
        expected = [3, 2]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_diff_minutes(self, backend_name, backend_factory, select_and_extract):
        """Test calculating difference in minutes between datetimes."""
        data = {
            "start": [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 1, 1, 14, 30, 0),
            ],
            "end": [
                datetime(2024, 1, 1, 13, 0, 0),
                datetime(2024, 1, 1, 16, 45, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Calculate difference in minutes
        expr = ma.col("end").dt.diff_minutes(ma.col("start"))
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "diff", backend_name)

        # 180 minutes, 135 minutes
        expected = [180, 135]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - DateTime Truncation
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestDateTimeTruncation:
    """Test truncating datetimes to different units."""

    def test_truncate_to_day(self, backend_name, backend_factory, select_and_extract):
        """Test truncating datetime to day (midnight)."""
        data = {
            "timestamp": [
                datetime(2024, 1, 15, 14, 35, 45),
                datetime(2024, 6, 20, 9, 15, 30),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Truncate to day
        expr = ma.col("timestamp").dt.truncate("1d")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [
            datetime(2024, 1, 15, 0, 0, 0),
            datetime(2024, 6, 20, 0, 0, 0)
        ]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_truncate_to_hour(self, backend_name, backend_factory, select_and_extract):
        """Test truncating datetime to hour."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite limitation: Hour-level truncation not supported")

        data = {
            "timestamp": [
                datetime(2024, 1, 15, 14, 35, 45),
                datetime(2024, 6, 20, 9, 15, 30),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Truncate to hour
        expr = ma.col("timestamp").dt.truncate("1h")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [
            datetime(2024, 1, 15, 14, 0, 0),
            datetime(2024, 6, 20, 9, 0, 0)
        ]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Flexible Offset Operations
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestFlexibleOffsetBy:
    """Test flexible duration offsets using string format."""

    def test_offset_add_days_and_hours(self, backend_name, backend_factory, select_and_extract):
        """Test adding combined duration (1 day 2 hours)."""
        data = {
            "timestamp": [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 6, 15, 14, 30, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Add 1 day 2 hours
        expr = ma.col("timestamp").dt.offset_by("1d2h")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [
            datetime(2024, 1, 2, 12, 0, 0),
            datetime(2024, 6, 16, 16, 30, 0)
        ]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_offset_subtract_months(self, backend_name, backend_factory, select_and_extract):
        """Test subtracting months."""
        if backend_name == "ibis-polars":
            pytest.xfail(
                "Ibis Polars backend doesn't support calendar-based intervals (months/years). "
                "Only duration-based intervals (days/hours/minutes/seconds) are supported."
            )

        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite limitation: Interval subtraction not supported")

        data = {
            "timestamp": [
                datetime(2024, 1, 1, 10, 0, 0),
                datetime(2024, 6, 15, 14, 30, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Subtract 3 months
        expr = ma.col("timestamp").dt.offset_by("-3mo")
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [
            datetime(2023, 10, 1, 10, 0, 0),
            datetime(2024, 3, 15, 14, 30, 0)
        ]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Integration Tests - Chaining Operations
# =============================================================================

@pytest.mark.integration
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestChainingTimeOperations:
    """Test chaining multiple temporal operations."""

    def test_chain_add_and_truncate(self, backend_name, backend_factory, select_and_extract):
        """Test chaining: add hours, add minutes, then truncate."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite limitation: Hour-level truncation not supported")

        data = {
            "timestamp": [datetime(2024, 1, 1, 10, 0, 0)]
        }
        df = backend_factory.create(data, backend_name)

        # Chain: Add 2 hours, add 30 minutes, truncate to hour
        # 10:00 + 2h = 12:00, + 30m = 12:30, truncate to hour = 12:00
        expr = (
            ma.col("timestamp")
            .dt.add_hours(2)
            .dt.add_minutes(30)
            .dt.truncate("1h")
        )
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [datetime(2024, 1, 1, 12, 0, 0)]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_chain_multiple_additions(self, backend_name, backend_factory, select_and_extract):
        """Test chaining multiple time additions."""
        data = {
            "timestamp": [datetime(2024, 1, 1, 10, 0, 0)]
        }
        df = backend_factory.create(data, backend_name)

        # Chain: Add 1 day, 2 hours, 30 minutes
        # 10:00 + 1d = next day 10:00, + 2h = 12:00, + 30m = 12:30
        expr = (
            ma.col("timestamp")
            .dt.add_days(1)
            .dt.add_hours(2)
            .dt.add_minutes(30)
        )
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [datetime(2024, 1, 2, 12, 30, 0)]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Edge Case Tests
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestTemporalEdgeCases:
    """Test edge cases for temporal operations."""

    def test_add_zero_hours(self, backend_name, backend_factory, select_and_extract):
        """Test adding zero hours (should return same timestamp)."""
        data = {
            "timestamp": [datetime(2024, 1, 1, 10, 30, 45)]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("timestamp").dt.add_hours(0)
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [datetime(2024, 1, 1, 10, 30, 45)]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_add_negative_hours(self, backend_name, backend_factory, select_and_extract):
        """Test adding negative hours (subtraction)."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite limitation: Negative time addition produces NaT")

        data = {
            "timestamp": [datetime(2024, 1, 1, 10, 30, 45)]
        }
        df = backend_factory.create(data, backend_name)

        # Add -2 hours (subtract 2 hours)
        expr = ma.col("timestamp").dt.add_hours(-2)
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "result", backend_name)

        expected = [datetime(2024, 1, 1, 8, 30, 45)]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )


# =============================================================================
# Cross-Backend Tests - Date/Time Extraction
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
])
class TestDateTimeExtraction:
    """Test extracting components from date/time values."""

    def test_extract_year(self, backend_name, backend_factory, select_and_extract):
        """Test extracting year from datetime."""
        data = {
            "timestamp": [
                datetime(2024, 3, 15, 10, 30, 45),
                datetime(2023, 12, 25, 14, 15, 30),
                datetime(2025, 1, 1, 0, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("timestamp").dt.year()
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "year", backend_name)

        expected = [2024, 2023, 2025]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_extract_month(self, backend_name, backend_factory, select_and_extract):
        """Test extracting month from datetime."""
        data = {
            "timestamp": [
                datetime(2024, 3, 15, 10, 30, 45),
                datetime(2024, 12, 25, 14, 15, 30),
                datetime(2024, 1, 1, 0, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("timestamp").dt.month()
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "month", backend_name)

        expected = [3, 12, 1]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_extract_day(self, backend_name, backend_factory, select_and_extract):
        """Test extracting day from datetime."""
        data = {
            "timestamp": [
                datetime(2024, 3, 15, 10, 30, 45),
                datetime(2024, 3, 25, 14, 15, 30),
                datetime(2024, 3, 1, 0, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("timestamp").dt.day()
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "day", backend_name)

        expected = [15, 25, 1]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_extract_hour(self, backend_name, backend_factory, select_and_extract):
        """Test extracting hour from datetime."""
        data = {
            "timestamp": [
                datetime(2024, 3, 15, 10, 30, 45),
                datetime(2024, 3, 15, 23, 15, 30),
                datetime(2024, 3, 15, 0, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("timestamp").dt.hour()
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "hour", backend_name)

        expected = [10, 23, 0]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_extract_minute(self, backend_name, backend_factory, select_and_extract):
        """Test extracting minute from datetime."""
        data = {
            "timestamp": [
                datetime(2024, 3, 15, 10, 30, 45),
                datetime(2024, 3, 15, 10, 45, 30),
                datetime(2024, 3, 15, 10, 0, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("timestamp").dt.minute()
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "minute", backend_name)

        expected = [30, 45, 0]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )

    def test_extract_second(self, backend_name, backend_factory, select_and_extract):
        """Test extracting second from datetime."""
        data = {
            "timestamp": [
                datetime(2024, 3, 15, 10, 30, 45),
                datetime(2024, 3, 15, 10, 30, 30),
                datetime(2024, 3, 15, 10, 30, 0),
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("timestamp").dt.second()
        backend_expr = expr.compile(df)

        actual = select_and_extract(df, backend_expr, "second", backend_name)

        expected = [45, 30, 0]
        assert actual == expected, (
            f"[{backend_name}] Expected {expected}, got {actual}"
        )
