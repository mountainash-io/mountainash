"""Cross-backend tests for datetime enrichment operations (Batch 6).

date(), time(), month_start(), month_end(), days_in_month().
"""

from datetime import date, datetime
import sqlite3

import pytest
import mountainash.expressions as ma
from fixtures.capability_gating import xfail_divergence


_SQLITE_TIME_SHIFT = (
    [xfail_divergence("IB-DT-14", backend="ibis-sqlite")]
    if sqlite3.sqlite_version_info < (3, 46)
    else []
)

POLARS_NARWHALS_IBIS = [
    "polars",
    "polars-lazy",
    pytest.param("pandas", marks=xfail_divergence("NW-DT-04", backend="pandas")),
    "narwhals-polars",
    pytest.param("narwhals-pandas", marks=xfail_divergence("NW-DT-04", backend="narwhals-pandas")),
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_AND_IBIS = [
    "polars",
    "polars-lazy",
    pytest.param("pandas", marks=xfail_divergence("NW-DT-05", backend="pandas")),
    pytest.param("narwhals-polars", marks=xfail_divergence("NW-DT-05", backend="narwhals-polars")),
    pytest.param("narwhals-pandas", marks=xfail_divergence("NW-DT-05", backend="narwhals-pandas")),
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_IBIS_DUCKDB_SQLITE = [
    "polars",
    "polars-lazy",
    pytest.param("pandas", marks=xfail_divergence("NW-DT-05", backend="pandas")),
    pytest.param("narwhals-polars", marks=xfail_divergence("NW-DT-05", backend="narwhals-polars")),
    pytest.param("narwhals-pandas", marks=xfail_divergence("NW-DT-05", backend="narwhals-pandas")),
    pytest.param("ibis-polars", marks=xfail_divergence("IB-DT-18", backend="ibis-polars")),
    "ibis-duckdb",
    pytest.param("ibis-sqlite", marks=_SQLITE_TIME_SHIFT),
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_NARWHALS_IBIS)
class TestDateExtraction:
    def test_date(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15, 10, 30), datetime(2024, 7, 20, 14, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.date()
        actual = collect_expr(df, expr)
        # Some backends return date objects, others return timestamps at midnight
        for i, (a, expected) in enumerate(zip(actual, [date(2024, 3, 15), date(2024, 7, 20)])):
            if hasattr(a, 'date'):
                a = a.date() if callable(a.date) else a.date
            assert a == expected, f"[{backend_name}] index {i}: got {a}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_AND_IBIS)
class TestTimeExtraction:
    def test_time(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15, 10, 30), datetime(2024, 7, 20, 14, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.time()
        actual = collect_expr(df, expr)
        assert len(actual) == 2, f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_AND_IBIS)
class TestMonthStart:
    def test_month_start(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15, 10, 30), datetime(2024, 7, 20, 14, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.month_start().dt.day()
        actual = collect_expr(df, expr)
        assert actual == [1, 1], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS_DUCKDB_SQLITE)
class TestMonthEnd:
    def test_month_end(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 2, 15), datetime(2024, 3, 15)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.month_end().dt.day()
        actual = collect_expr(df, expr)
        assert actual == [29, 31], f"[{backend_name}] got {actual}"  # 2024 is leap year


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS_DUCKDB_SQLITE)
class TestDaysInMonth:
    def test_days_in_month(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 2, 15), datetime(2024, 3, 15)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.days_in_month()
        actual = collect_expr(df, expr)
        assert actual == [29, 31], f"[{backend_name}] got {actual}"
