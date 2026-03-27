"""
Cross-backend tests for natural language temporal filtering.

Tests natural language time expressions like:
- "last 3 minutes" (journalctl --since style)
- "older than 7 days" (find -mtime style)
- "between 2 hours and 1 hour ago"

These tests validate that temporal filtering works consistently across
all backends: Polars, Pandas, Narwhals, and Ibis (DuckDB, Polars, SQLite).
"""

import pytest
from datetime import datetime, timedelta
import mountainash_expressions as ma
from mountainash.expressions.core.utils.temporal import (
    parse_time_expression,
    to_timedelta,
    to_offset_string,
    time_ago,
    within_last,
    older_than,
    between_last,
)


# =============================================================================
# Unit Tests - Parsing and Conversion (Backend-Independent)
# =============================================================================

@pytest.mark.unit
@pytest.mark.temporal
class TestTimeExpressionParsing:
    """Test parsing of natural language time expressions."""

    def test_parse_various_formats(self):
        """Test parsing various time expression formats."""
        # Minutes
        assert parse_time_expression("3 minutes") == (3, 'minutes')
        assert parse_time_expression("3minutes") == (3, 'minutes')
        assert parse_time_expression("3m") == (3, 'minutes')

        # Hours
        assert parse_time_expression("2 hours") == (2, 'hours')
        assert parse_time_expression("2h") == (2, 'hours')

        # Days
        assert parse_time_expression("1 day") == (1, 'days')
        assert parse_time_expression("7 days") == (7, 'days')
        assert parse_time_expression("7d") == (7, 'days')

    def test_timedelta_conversion(self):
        """Test conversion to Python timedelta."""
        assert to_timedelta("5 minutes") == timedelta(minutes=5)
        assert to_timedelta("2 hours") == timedelta(hours=2)
        assert to_timedelta("3 days") == timedelta(days=3)
        assert to_timedelta("1 week") == timedelta(weeks=1)

        # Approximate conversions
        assert to_timedelta("1 month") == timedelta(days=30)
        assert to_timedelta("1 year") == timedelta(days=365)

    def test_offset_string_conversion(self):
        """Test conversion to Polars/backend offset strings."""
        assert to_offset_string("3 minutes") == "3m"
        assert to_offset_string("2 hours") == "2h"
        assert to_offset_string("7 days") == "7d"
        assert to_offset_string("2 weeks") == "2w"
        assert to_offset_string("3 months") == "3mo"
        assert to_offset_string("1 year") == "1y"


# =============================================================================
# Cross-Backend Tests - Temporal Filtering
# =============================================================================

@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite"
])
class TestWithinLastFilter:
    """Test 'within last X time' filtering across all backends."""

    def test_within_last_minutes(
        self,
        backend_name,
        backend_factory,
        get_result_count,
        get_column_values,
        select_and_extract
    ):
        """Test filtering for 'last X minutes' like journalctl --since."""

        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "SQLite has no native datetime type. Sub-day datetime comparisons "
                "via Ibis produce incorrect results because values are compared as "
                "strings rather than timestamps. All 4 rows pass the gt() filter."
            )

        now = datetime.now()
        data = {
            "timestamp": [
                now - timedelta(minutes=2),   # 2 minutes ago
                now - timedelta(minutes=5),   # 5 minutes ago
                now - timedelta(minutes=10),  # 10 minutes ago
                now - timedelta(minutes=30),  # 30 minutes ago
            ],
            "message": ["A", "B", "C", "D"]
        }

        # Create DataFrame for backend
        df = backend_factory.create(data, backend_name)

        # Filter: last 8 minutes
        expr = within_last(ma.col("timestamp"), "8 minutes")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        print(select_and_extract(df, backend_expr, "formatted", backend_name))

        # Should get messages A, B (within 8 minutes)
        # Message C (10 min) and D (30 min) are older
        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows, got {count}"

        messages = get_column_values(result, "message", backend_name)
        assert messages == ["A", "B"], (
            f"[{backend_name}] Expected ['A', 'B'], got {messages}"
        )


@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite"
])
class TestOlderThanFilter:
    """Test 'older than X time' filtering across all backends."""

    def test_older_than_days(
        self,
        backend_name,
        backend_factory,
        get_result_count,
        get_column_values
    ):
        """Test filtering for 'older than X' like find -mtime."""
        now = datetime.now()
        data = {
            "created_at": [
                now - timedelta(days=1),   # 1 day ago
                now - timedelta(days=5),   # 5 days ago
                now - timedelta(days=10),  # 10 days ago
                now - timedelta(days=30),  # 30 days ago
            ],
            "file": ["A", "B", "C", "D"]
        }

        # Create DataFrame for backend
        df = backend_factory.create(data, backend_name)

        # Filter: older than 7 days
        expr = older_than(ma.col("created_at"), "7 days")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        # Should get files C, D (older than 7 days)
        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows, got {count}"

        files = get_column_values(result, "file", backend_name)
        assert files == ["C", "D"], (
            f"[{backend_name}] Expected ['C', 'D'], got {files}"
        )


@pytest.mark.cross_backend
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite"
])
class TestBetweenLastFilter:
    """Test 'between X and Y ago' filtering across all backends."""

    def test_between_two_time_ranges(
        self,
        backend_name,
        backend_factory,
        get_result_count,
        get_column_values
    ):

        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "SQLite has no native datetime type. Sub-day datetime comparisons "
                "via Ibis produce incorrect results (string vs timestamp comparison). "
                "The between range filter returns 0 rows instead of 2."
            )

        """Test filtering for 'between X and Y ago'."""
        now = datetime.now()
        data = {
            "timestamp": [
                now - timedelta(hours=1),   # 1 hour ago
                now - timedelta(hours=3),   # 3 hours ago
                now - timedelta(hours=6),   # 6 hours ago
                now - timedelta(hours=12),  # 12 hours ago
            ],
            "event": ["A", "B", "C", "D"]
        }

        # Create DataFrame for backend
        df = backend_factory.create(data, backend_name)

        # Filter: between 8 hours ago and 2 hours ago
        expr = between_last(ma.col("timestamp"), "8 hours", "2 hours")
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        # Should get events B, C (between 8h and 2h ago)
        # Event A (1h) is too recent, D (12h) is too old
        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows, got {count}"

        events = get_column_values(result, "event", backend_name)
        assert events == ["B", "C"], (
            f"[{backend_name}] Expected ['B', 'C'], got {events}"
        )


# =============================================================================
# Integration Tests - Real-World Scenarios
# =============================================================================

@pytest.mark.integration
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite"
])
class TestRealWorldLogFiltering:
    """Test realistic log filtering scenarios."""

    def test_show_recent_errors(
        self,
        backend_name,
        backend_factory,
        get_result_count,
        get_column_values
    ):
        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "SQLite has no native datetime type. Sub-day datetime comparisons "
                "via Ibis produce incorrect results (string vs timestamp comparison). "
                "The within_last filter passes too many rows (3 instead of 2)."
            )


        """Test filtering errors from last X minutes (like journalctl)."""
        now = datetime.now()
        logs_data = {
            "timestamp": [
                now - timedelta(minutes=1),
                now - timedelta(minutes=3),
                now - timedelta(minutes=5),
                now - timedelta(minutes=10),
                now - timedelta(minutes=30),
                now - timedelta(hours=2),
            ],
            "level": ["ERROR", "INFO", "ERROR", "WARN", "INFO", "ERROR"],
            "message": [
                "Database connection failed",
                "Request processed",
                "Timeout error",
                "Slow query detected",
                "Startup complete",
                "Old error",
            ]
        }

        # Create DataFrame for backend
        logs = backend_factory.create(logs_data, backend_name)

        # Scenario: Show errors from last 15 minutes (like journalctl)
        expr = (
            (ma.col("level") == ma.lit("ERROR")) &
            within_last(ma.col("timestamp"), "15 minutes")
        )
        backend_expr = expr.compile(logs)
        recent_errors = logs.filter(backend_expr)

        count = get_result_count(recent_errors, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 recent errors, got {count}"

        messages = get_column_values(recent_errors, "message", backend_name)
        assert messages == [
            "Database connection failed",
            "Timeout error"
        ], f"[{backend_name}] Unexpected error messages: {messages}"

    def test_cleanup_old_logs(
        self,
        backend_name,
        backend_factory,
        get_result_count,
        get_column_values
    ):
        if backend_name == "ibis-sqlite":
            pytest.xfail(
                "SQLite has no native datetime type. Sub-day datetime comparisons "
                "via Ibis produce incorrect results (string vs timestamp comparison). "
                "The older_than filter returns 0 rows instead of 1."
            )

        """Test identifying old logs for cleanup (older than 1 hour)."""
        now = datetime.now()
        logs_data = {
            "timestamp": [
                now - timedelta(minutes=1),
                now - timedelta(minutes=3),
                now - timedelta(minutes=5),
                now - timedelta(minutes=10),
                now - timedelta(minutes=30),
                now - timedelta(hours=2),
            ],
            "level": ["ERROR", "INFO", "ERROR", "WARN", "INFO", "ERROR"],
            "message": [
                "Database connection failed",
                "Request processed",
                "Timeout error",
                "Slow query detected",
                "Startup complete",
                "Old error",
            ]
        }

        # Create DataFrame for backend
        logs = backend_factory.create(logs_data, backend_name)

        # Scenario: Cleanup old logs (older than 1 hour)
        expr = older_than(ma.col("timestamp"), "1 hour")
        backend_expr = expr.compile(logs)
        old_logs = logs.filter(backend_expr)

        count = get_result_count(old_logs, backend_name)
        assert count == 1, f"[{backend_name}] Expected 1 old log, got {count}"

        messages = get_column_values(old_logs, "message", backend_name)
        assert messages == ["Old error"], (
            f"[{backend_name}] Expected ['Old error'], got {messages}"
        )


@pytest.mark.integration
@pytest.mark.temporal
@pytest.mark.parametrize("backend_name", [
    "polars",
    "pandas",
    "narwhals",
    "ibis-duckdb",
    "ibis-polars",
    "ibis-sqlite"
])
class TestChainingTemporalWithOtherOperations:
    """Test that temporal filters chain with other operations."""

    def test_complex_multi_condition_filter(
        self,
        backend_name,
        backend_factory,
        get_result_count,
        get_column_values
    ):
        """Test complex filter: recent + active + high value."""
        now = datetime.now()
        data = {
            "timestamp": [
                now - timedelta(minutes=2),
                now - timedelta(minutes=5),
                now - timedelta(minutes=10),
            ],
            "value": [100, 200, 300],
            "status": ["active", "active", "inactive"]
        }

        # Create DataFrame for backend
        df = backend_factory.create(data, backend_name)

        # Complex filter: recent + active + high value
        expr = (
            within_last(ma.col("timestamp"), "8 minutes") &
            (ma.col("status") == ma.lit("active")) &
            (ma.col("value") > 150)
        )
        backend_expr = expr.compile(df)
        result = df.filter(backend_expr)

        # Should only get the middle row (5 min ago, active, value=200)
        count = get_result_count(result, backend_name)
        assert count == 1, f"[{backend_name}] Expected 1 row, got {count}"

        values = get_column_values(result, "value", backend_name)
        assert values == [200], (
            f"[{backend_name}] Expected [200], got {values}"
        )
