"""
Comprehensive tests for temporal operations across backends.

Tests: Date/time extraction (YEAR, MONTH, DAY, etc.) and date arithmetic (ADD_DAYS, DIFF_DAYS, etc.).
"""

import polars as pl
import narwhals as nw
import ibis
from datetime import datetime, date
import mountainash_expressions as ma


def test_datetime_extraction():
    """Test datetime component extraction operations."""
    df = pl.DataFrame({
        "timestamp": [
            datetime(2024, 1, 15, 14, 30, 45),
            datetime(2024, 3, 20, 9, 15, 30),
            datetime(2024, 6, 10, 18, 45, 10),
            datetime(2024, 12, 25, 23, 59, 59),
        ]
    })

    # Test: Year extraction
    expr = ma.col("timestamp").dt_year()
    result = df.select(expr.compile(df).alias("year"))
    assert result["year"].to_list() == [2024, 2024, 2024, 2024]

    # Test: Month extraction
    expr = ma.col("timestamp").dt_month()
    result = df.select(expr.compile(df).alias("month"))
    assert result["month"].to_list() == [1, 3, 6, 12]

    # Test: Day extraction
    expr = ma.col("timestamp").dt_day()
    result = df.select(expr.compile(df).alias("day"))
    assert result["day"].to_list() == [15, 20, 10, 25]

    # Test: Hour extraction
    expr = ma.col("timestamp").dt_hour()
    result = df.select(expr.compile(df).alias("hour"))
    assert result["hour"].to_list() == [14, 9, 18, 23]

    # Test: Minute extraction
    expr = ma.col("timestamp").dt_minute()
    result = df.select(expr.compile(df).alias("minute"))
    assert result["minute"].to_list() == [30, 15, 45, 59]

    # Test: Second extraction
    expr = ma.col("timestamp").dt_second()
    result = df.select(expr.compile(df).alias("second"))
    assert result["second"].to_list() == [45, 30, 10, 59]


def test_date_extraction():
    """Test date component extraction (weekday, week, quarter)."""
    df = pl.DataFrame({
        "date": [
            date(2024, 1, 1),   # Monday, Week 1, Q1
            date(2024, 4, 15),  # Monday, Week 16, Q2
            date(2024, 7, 20),  # Saturday, Week 29, Q3
            date(2024, 10, 31), # Thursday, Week 44, Q4
        ]
    })

    # Test: Weekday extraction (0=Monday, 6=Sunday)
    expr = ma.col("date").dt_weekday()
    result = df.select(expr.compile(df).alias("weekday"))
    # 2024-01-01 is Monday (0), 2024-04-15 is Monday (0), 2024-07-20 is Saturday (5), 2024-10-31 is Thursday (3)
    assert result["weekday"].to_list() == [0, 0, 5, 3]

    # Test: Week number extraction
    expr = ma.col("date").dt_week()
    result = df.select(expr.compile(df).alias("week"))
    # Week numbers: 1, 16, 29, 44
    assert result["week"].to_list() == [1, 16, 29, 44]

    # Test: Quarter extraction
    expr = ma.col("date").dt_quarter()
    result = df.select(expr.compile(df).alias("quarter"))
    assert result["quarter"].to_list() == [1, 2, 3, 4]


def test_date_arithmetic_add_days():
    """Test adding days to dates."""
    df = pl.DataFrame({
        "date": [
            date(2024, 1, 1),
            date(2024, 2, 28),  # Leap year
            date(2024, 12, 25),
        ]
    })

    # Test: Add 7 days
    expr = ma.col("date").dt_add_days(7)
    result = df.select(expr.compile(df).alias("result"))
    expected = [date(2024, 1, 8), date(2024, 3, 6), date(2025, 1, 1)]
    assert result["result"].to_list() == expected


def test_date_arithmetic_add_months():
    """Test adding months to dates."""
    df = pl.DataFrame({
        "date": [
            date(2024, 1, 15),
            date(2024, 6, 30),
            date(2024, 11, 10),
        ]
    })

    # Test: Add 3 months
    expr = ma.col("date").dt_add_months(3)
    result = df.select(expr.compile(df).alias("result"))
    expected = [date(2024, 4, 15), date(2024, 9, 30), date(2025, 2, 10)]
    assert result["result"].to_list() == expected


def test_date_arithmetic_add_years():
    """Test adding years to dates."""
    df = pl.DataFrame({
        "date": [
            date(2024, 1, 1),
            date(2024, 2, 29),  # Leap year date
            date(2024, 12, 31),
        ]
    })

    # Test: Add 1 year
    expr = ma.col("date").dt_add_years(1)
    result = df.select(expr.compile(df).alias("result"))
    expected = [date(2025, 1, 1), date(2025, 2, 28), date(2025, 12, 31)]
    assert result["result"].to_list() == expected


def test_date_difference():
    """Test calculating date differences in days."""
    df = pl.DataFrame({
        "start_date": [
            date(2024, 1, 1),
            date(2024, 6, 1),
            date(2024, 12, 1),
        ],
        "end_date": [
            date(2024, 1, 8),
            date(2024, 6, 30),
            date(2025, 1, 1),
        ]
    })

    # Test: Calculate difference (end_date - start_date)
    expr = ma.col("end_date").dt_diff_days(ma.col("start_date"))
    result = df.select(expr.compile(df).alias("diff_days"))
    assert result["diff_days"].to_list() == [7, 29, 31]


def test_temporal_with_filtering():
    """Test temporal operations combined with filtering."""
    df = pl.DataFrame({
        "date": [
            date(2024, 1, 15),
            date(2024, 6, 20),
            date(2024, 9, 10),
            date(2024, 12, 25),
        ],
        "value": [100, 200, 300, 400]
    })

    # Test: Filter dates in Q3 (quarter = 3)
    expr = ma.col("date").dt_quarter() == 3
    result = df.filter(expr.compile(df))
    assert len(result) == 1
    assert result["value"].to_list() == [300]

    # Test: Filter January dates (month = 1)
    expr = ma.col("date").dt_month() == 1
    result = df.filter(expr.compile(df))
    assert len(result) == 1
    assert result["value"].to_list() == [100]


def test_temporal_chaining():
    """Test chaining temporal operations with other operations."""
    df = pl.DataFrame({
        "timestamp": [
            datetime(2024, 1, 15, 14, 30, 0),
            datetime(2024, 6, 20, 9, 15, 0),
            datetime(2024, 9, 10, 18, 45, 0),
        ],
        "name": ["Alice", "Bob", "Charlie"]
    })

    # Test: Extract year, then filter
    expr = ma.col("timestamp").dt_year()
    result = df.select(expr.compile(df).alias("year"))
    assert all(year == 2024 for year in result["year"].to_list())

    # Test: Extract month, compare, and filter
    expr = (ma.col("timestamp").dt_month() >= 6)
    result = df.filter(expr.compile(df))
    assert result["name"].to_list() == ["Bob", "Charlie"]


def test_cross_backend_temporal_compatibility():
    """Test that temporal operations produce same results across backends."""
    data = {
        "date": [
            date(2024, 1, 15),
            date(2024, 6, 20),
            date(2024, 9, 10),
            date(2024, 12, 25),
        ],
        "value": [10, 20, 30, 40]
    }

    # Polars
    df_polars = pl.DataFrame(data)

    # Narwhals (wrapping Polars)
    df_narwhals = nw.from_native(df_polars)

    # Ibis
    con_ibis = ibis.duckdb.connect()
    df_ibis = con_ibis.create_table("test_temporal_cross", data)

    # Test 1: Year extraction
    expr = ma.col("date").dt_year()

    result_polars = df_polars.select(expr.compile(df_polars).alias("year"))
    result_narwhals = df_narwhals.select(expr.compile(df_narwhals).alias("year"))
    ibis_expr = expr.compile(df_ibis).name("year")
    result_ibis = df_ibis.select(ibis_expr).execute()

    expected = [2024, 2024, 2024, 2024]
    assert result_polars["year"].to_list() == expected
    assert result_narwhals["year"].to_list() == expected
    assert result_ibis["year"].tolist() == expected

    # Test 2: Month extraction
    expr = ma.col("date").dt_month()

    result_polars = df_polars.select(expr.compile(df_polars).alias("month"))
    result_narwhals = df_narwhals.select(expr.compile(df_narwhals).alias("month"))
    ibis_expr = expr.compile(df_ibis).name("month")
    result_ibis = df_ibis.select(ibis_expr).execute()

    expected = [1, 6, 9, 12]
    assert result_polars["month"].to_list() == expected
    assert result_narwhals["month"].to_list() == expected
    assert result_ibis["month"].tolist() == expected

    # Test 3: Quarter extraction
    expr = ma.col("date").dt_quarter()

    result_polars = df_polars.select(expr.compile(df_polars).alias("quarter"))
    result_narwhals = df_narwhals.select(expr.compile(df_narwhals).alias("quarter"))
    ibis_expr = expr.compile(df_ibis).name("quarter")
    result_ibis = df_ibis.select(ibis_expr).execute()

    expected = [1, 2, 3, 4]
    assert result_polars["quarter"].to_list() == expected
    assert result_narwhals["quarter"].to_list() == expected
    assert result_ibis["quarter"].tolist() == expected


if __name__ == "__main__":
    print("Running temporal operation tests...")

    print("✓ test_datetime_extraction")
    test_datetime_extraction()

    print("✓ test_date_extraction")
    test_date_extraction()

    print("✓ test_date_arithmetic_add_days")
    test_date_arithmetic_add_days()

    print("✓ test_date_arithmetic_add_months")
    test_date_arithmetic_add_months()

    print("✓ test_date_arithmetic_add_years")
    test_date_arithmetic_add_years()

    print("✓ test_date_difference")
    test_date_difference()

    print("✓ test_temporal_with_filtering")
    test_temporal_with_filtering()

    print("✓ test_temporal_chaining")
    test_temporal_chaining()

    print("✓ test_cross_backend_temporal_compatibility")
    test_cross_backend_temporal_compatibility()

    print("\n✅ All temporal tests passed!")
