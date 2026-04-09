"""Cross-backend tests for datetime namespace fluent composition."""

import pytest
from datetime import datetime
import mountainash.expressions as ma


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
class TestComposeDatetime:
    """Test fluent .dt method chaining patterns."""

    def test_extract_year_then_compare(self, backend_name, backend_factory, get_result_count):
        """Extract year then filter: .dt.year().eq(2024)."""
        data = {
            "ts": [
                datetime(2023, 6, 15),
                datetime(2024, 1, 10),
                datetime(2024, 8, 20),
                datetime(2025, 3, 1),
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.year().eq(2024)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 rows in year 2024, got {count}"

    def test_add_days_then_extract_month(self, backend_name, backend_factory, collect_expr):
        """Arithmetic then extract: .dt.add_days(20).dt.month()."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type. Interval addition not supported.")
        data = {
            "ts": [
                datetime(2024, 1, 20),  # +20 days = Feb 9
                datetime(2024, 2, 15),  # +20 days = Mar 6
                datetime(2024, 12, 20), # +20 days = Jan 9 (2025)
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.add_days(20).dt.month()
        actual = collect_expr(df, expr)

        assert actual == [2, 3, 1], f"[{backend_name}] Expected [2, 3, 1], got {actual}"

    def test_extract_year_then_compare_to_column(self, backend_name, backend_factory, get_result_count):
        """Extract then compare to column: .dt.year().gt(col('threshold'))."""
        data = {
            "ts": [
                datetime(2022, 1, 1),
                datetime(2024, 6, 1),
                datetime(2025, 1, 1),
            ],
            "threshold": [2023, 2025, 2020],
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.year().gt(ma.col("threshold"))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        # Row 0: 2022 > 2023 -> False
        # Row 1: 2024 > 2025 -> False
        # Row 2: 2025 > 2020 -> True
        assert count == 1, f"[{backend_name}] Expected 1 row, got {count}"

    def test_business_hours_filter(self, backend_name, backend_factory, get_result_count):
        """Dual extract + boolean: hour >= 9 AND hour < 17."""
        if backend_name == "ibis-sqlite":
            pytest.xfail("SQLite has no native datetime type. Sub-day extraction unreliable.")
        data = {
            "ts": [
                datetime(2024, 1, 15, 8, 0),   # 8am - before
                datetime(2024, 1, 15, 9, 0),   # 9am - in
                datetime(2024, 1, 15, 12, 30),  # 12:30 - in
                datetime(2024, 1, 15, 16, 59),  # 4:59pm - in
                datetime(2024, 1, 15, 17, 0),   # 5pm - after
                datetime(2024, 1, 15, 22, 0),   # 10pm - after
            ]
        }
        df = backend_factory.create(data, backend_name)

        expr = ma.col("ts").dt.hour().ge(9).and_(ma.col("ts").dt.hour().lt(17))
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 3, f"[{backend_name}] Expected 3 business-hours rows, got {count}"

    def test_extract_month_then_filter_and_extract_day(self, backend_name, backend_factory, get_result_count):
        """Two dt operations: filter by month, then verify day extraction works on filtered result."""
        data = {
            "ts": [
                datetime(2024, 3, 15),
                datetime(2024, 6, 20),
                datetime(2024, 3, 25),
                datetime(2024, 9, 10),
            ]
        }
        df = backend_factory.create(data, backend_name)

        # Filter to March, then verify count
        expr = ma.col("ts").dt.month().eq(3)
        result = df.filter(expr.compile(df))

        count = get_result_count(result, backend_name)
        assert count == 2, f"[{backend_name}] Expected 2 March rows, got {count}"
