"""Cross-backend tests for datetime enrichment operations (Batch 6).

date(), time(), month_start(), month_end(), days_in_month().
"""

from datetime import date, datetime

import pytest
import mountainash.expressions as ma
from pyarrow.lib import ArrowNotImplementedError
from fixtures.call_expectations import expect_call_failure


POLARS_NARWHALS_IBIS = [
    "polars",
    "polars-lazy",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_AND_IBIS = [
    "polars",
    "polars-lazy",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_AND_IBIS_TIME = [
    "polars",
    "polars-lazy",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]

POLARS_IBIS_DUCKDB_SQLITE = [
    "polars",
    "polars-lazy",
    "pandas",
    "narwhals-polars",
    "narwhals-pandas",
    "ibis-polars",
    "ibis-duckdb",
    "ibis-sqlite",
]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_NARWHALS_IBIS)
class TestDateExtraction:
    def test_date(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15, 10, 30), datetime(2024, 7, 20, 14, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.date()
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-pandas'),
            reason='dt.date() raises on pandas and narwhals-pandas',
            errors=(NotImplementedError,),
        ):
            actual = collect_expr(df, expr)
            # Some backends return date objects, others return timestamps at midnight
            for i, (a, expected) in enumerate(zip(actual, [date(2024, 3, 15), date(2024, 7, 20)])):
                if hasattr(a, "date"):
                    a = a.date() if callable(a.date) else a.date
                assert a == expected, f"[{backend_name}] index {i}: got {a}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_AND_IBIS_TIME)
class TestTimeExtraction:
    def test_time(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15, 10, 30), datetime(2024, 7, 20, 14, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.time()
        with expect_call_failure(
            when=backend_name == 'ibis-sqlite' or backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas'),
            reason=('dt.time() yields the wrong type on ibis-sqlite' if backend_name == 'ibis-sqlite' else 'datetime enrichment operations raise on pandas/narwhals'),
            errors=((ArrowNotImplementedError,) if backend_name == 'ibis-sqlite' else (NotImplementedError,)),
        ):
            actual = collect_expr(df, expr)
            assert len(actual) == 2, f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_AND_IBIS)
class TestMonthStart:
    def test_month_start(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 3, 15, 10, 30), datetime(2024, 7, 20, 14, 0)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.month_start().dt.day()
        with expect_call_failure(
            when=backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas'),
            reason='datetime enrichment operations raise on pandas/narwhals',
            errors=(NotImplementedError,),
        ):
            actual = collect_expr(df, expr)
            assert actual == [1, 1], f"[{backend_name}] got {actual}"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS_DUCKDB_SQLITE)
class TestMonthEnd:
    def test_month_end(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 2, 15), datetime(2024, 3, 15)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.month_end().dt.day()
        with expect_call_failure(
            when=backend_name == 'ibis-polars' or backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas'),
            reason=('month_end()/days_in_month() raise on ibis-polars' if backend_name == 'ibis-polars' else 'datetime enrichment operations raise on pandas/narwhals'),
            errors=((TypeError,) if backend_name == 'ibis-polars' else (NotImplementedError,)),
        ):
            actual = collect_expr(df, expr)
            assert actual == [29, 31], f"[{backend_name}] got {actual}"  # 2024 is leap year


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", POLARS_IBIS_DUCKDB_SQLITE)
class TestDaysInMonth:
    def test_days_in_month(self, backend_name, backend_factory, collect_expr):
        data = {"ts": [datetime(2024, 2, 15), datetime(2024, 3, 15)]}
        df = backend_factory.create(data, backend_name)
        expr = ma.col("ts").dt.days_in_month()
        with expect_call_failure(
            when=backend_name == 'ibis-polars' or backend_name in ('pandas', 'narwhals-polars', 'narwhals-pandas'),
            reason=('month_end()/days_in_month() raise on ibis-polars' if backend_name == 'ibis-polars' else 'datetime enrichment operations raise on pandas/narwhals'),
            errors=((TypeError,) if backend_name == 'ibis-polars' else (NotImplementedError,)),
        ):
            actual = collect_expr(df, expr)
            assert actual == [29, 31], f"[{backend_name}] got {actual}"
