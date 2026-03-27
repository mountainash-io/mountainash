"""Shared fixtures for reshape module tests."""

import pytest
import pandas as pd
import polars as pl
import pyarrow as pa
import ibis
import narwhals as nw
from typing import Dict, List, Any

from mountainash.dataframes import DataFrameUtils

@pytest.fixture(scope="module")
def sample_data_standard() -> Dict[str, List[Any]]:
    """Standard test data used across all backend fixtures."""
    return {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "category": ["A", "B", "A", "C", "B"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8],
        "active": [True, False, True, True, False]
    }


@pytest.fixture
def sample_polars_lazyframe(sample_data_standard) -> pl.LazyFrame:
    """Polars LazyFrame for lazy evaluation testing."""
    return pl.DataFrame(sample_data_standard).lazy()


@pytest.fixture
def sample_narwhals_df(sample_data_standard) -> nw.DataFrame:
    """Narwhals DataFrame wrapping pandas for universal backend testing."""
    pandas_df = pd.DataFrame(sample_data_standard)
    return nw.from_native(pandas_df)


@pytest.fixture
def sample_narwhals_lazyframe(sample_polars_lazyframe) -> nw.LazyFrame:
    """Narwhals LazyFrame wrapping Polars LazyFrame for lazy evaluation testing."""
    return nw.from_native(sample_polars_lazyframe)


@pytest.fixture
def large_dataframe_for_batching() -> pd.DataFrame:
    """Large pandas DataFrame (100 rows) for split_in_batches testing."""
    return pd.DataFrame({
        "id": list(range(1, 101)),
        "value": [i * 10.5 for i in range(1, 101)],
        "category": [f"Cat_{i % 5}" for i in range(1, 101)]
    })


@pytest.fixture
def large_polars_df_for_batching() -> pl.DataFrame:
    """Large Polars DataFrame (100 rows) for split_in_batches testing."""
    return pl.DataFrame({
        "id": list(range(1, 101)),
        "value": [i * 10.5 for i in range(1, 101)],
        "category": [f"Cat_{i % 5}" for i in range(1, 101)]
    })


@pytest.fixture
def large_polars_lazyframe_for_batching() -> pl.LazyFrame:
    """Large Polars LazyFrame (100 rows) for split_in_batches testing."""
    return pl.DataFrame({
        "id": list(range(1, 101)),
        "value": [i * 10.5 for i in range(1, 101)],
        "category": [f"Cat_{i % 5}" for i in range(1, 101)]
    }).lazy()


@pytest.fixture
def large_pyarrow_table_for_batching() -> pa.Table:
    """Large PyArrow Table (100 rows) for split_in_batches testing."""
    return pa.table({
        "id": list(range(1, 101)),
        "value": [i * 10.5 for i in range(1, 101)],
        "category": [f"Cat_{i % 5}" for i in range(1, 101)]
    })


@pytest.fixture
def large_ibis_table_for_batching() -> Any:
    """Large Ibis Table (100 rows) for split_in_batches testing."""
    data = {
        "id": list(range(1, 101)),
        "value": [i * 10.5 for i in range(1, 101)],
        "category": [f"Cat_{i % 5}" for i in range(1, 101)]
    }
    return DataFrameUtils.create_ibis(data)


@pytest.fixture
def large_narwhals_df_for_batching(large_polars_df_for_batching) -> nw.DataFrame:
    """Large Narwhals DataFrame (100 rows) for split_in_batches testing."""
    return nw.from_native(large_polars_df_for_batching)


@pytest.fixture
def large_narwhals_lazyframe_for_batching(large_polars_lazyframe_for_batching) -> nw.LazyFrame:
    """Large Narwhals LazyFrame (100 rows) for split_in_batches testing."""
    return nw.from_native(large_polars_lazyframe_for_batching)


@pytest.fixture
def dataframe_with_special_columns() -> pd.DataFrame:
    """DataFrame with columns that need careful handling (spaces, special chars)."""
    return pd.DataFrame({
        "column with spaces": [1, 2, 3],
        "column-with-dashes": ["a", "b", "c"],
        "column_normal": [10.5, 20.5, 30.5],
        "🚀_emoji_col": [True, False, True]
    })


@pytest.fixture
def empty_dataframes() -> Dict[str, Any]:
    """Empty DataFrames for all backends to test edge cases."""
    return {
        "pandas": DataFrameUtils.create_pandas({}),
        "polars": DataFrameUtils.create_polars({}),
        "pyarrow": DataFrameUtils.create_pyarrow({}),
        "ibis": DataFrameUtils.create_ibis({}),
        "narwhals": nw.from_native(pd.DataFrame({}))

    }

@pytest.fixture
def single_row_dataframes() -> Dict[str, Any]:
    """Single-row DataFrames for all backends."""
    data = {"id": [1], "name": ["Alice"], "value": [100.5]}
    return {
        "pandas": pd.DataFrame(data),
        "polars": pl.DataFrame(data),
        "pyarrow": pa.table(data),
        "ibis": DataFrameUtils.create_ibis(data),
        "narwhals": nw.from_native(pd.DataFrame(data))
    }


@pytest.fixture
def single_column_dataframes() -> Dict[str, Any]:
    """Single-column DataFrames for all backends."""
    data = {"id": [1, 2, 3, 4, 5]}
    return {
        "pandas": pd.DataFrame(data),
        "polars": pl.DataFrame(data),
        "pyarrow": pa.table(data),
        "ibis": DataFrameUtils.create_ibis(data),
        "narwhals": nw.from_native(pd.DataFrame(data))

    }


@pytest.fixture(scope="module")
def all_backend_dataframes(sample_data_standard):
    """All backend DataFrames with identical data for cross-backend consistency testing."""
    # Create real ibis table using DuckDB backend
    # ibis.set_backend("polars")
    # ibis_backend = ibis.backends.polars.connect()
    # ibis_table = ibis_backend.create_table("test_cross_backend", sample_data_standard, overwrite=True)
    ibis_table = DataFrameUtils.create_ibis(sample_data_standard)  # Ensure table exists


    return {
        "pandas": pd.DataFrame(sample_data_standard),
        "polars": pl.DataFrame(sample_data_standard),
        "polars_lazy": pl.DataFrame(sample_data_standard).lazy(),
        "pyarrow": pa.table(sample_data_standard),
        "ibis": ibis_table,
        "narwhals": nw.from_native(pd.DataFrame(sample_data_standard))
    }


@pytest.fixture
def dataframe_with_nulls() -> Dict[str, Any]:
    """DataFrames with null values for testing null handling."""
    data = {
        "id": [1, 2, None, 4, 5],
        "name": ["Alice", None, "Charlie", "Diana", None],
        "value": [100.5, None, 300.9, None, 500.8]
    }
    return {
        "pandas": pd.DataFrame(data),
        "polars": pl.DataFrame(data)
    }


@pytest.fixture
def rename_mapping_valid() -> Dict[str, str]:
    """Valid column rename mapping for testing."""
    return {
        "id": "identifier",
        "name": "full_name",
        "value": "amount"
    }


@pytest.fixture
def rename_mapping_invalid_duplicate() -> Dict[str, str]:
    """Invalid rename mapping with duplicate target names."""
    return {
        "id": "new_col",
        "name": "new_col",  # Duplicate!
        "value": "amount"
    }


@pytest.fixture
def rename_mapping_nonexistent() -> Dict[str, str]:
    """Rename mapping referencing nonexistent columns."""
    return {
        "nonexistent_col": "new_name",
        "another_fake": "another_new"
    }


# Group_by fixtures for testing reshape operations on grouped dataframes
@pytest.fixture
def grouped_pandas_df() -> Any:
    """Pandas DataFrame with group_by applied."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "C", "B", "A"],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8, 600.1],
        "active": [True, False, True, True, False, True]
    }
    df = pd.DataFrame(data)
    return df.groupby("category")


@pytest.fixture
def grouped_polars_df() -> Any:
    """Polars DataFrame with group_by applied."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "C", "B", "A"],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8, 600.1],
        "active": [True, False, True, True, False, True]
    }
    df = pl.DataFrame(data)
    return df.group_by("category")


@pytest.fixture
def grouped_polars_lazyframe() -> Any:
    """Polars LazyFrame with group_by applied."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "C", "B", "A"],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8, 600.1],
        "active": [True, False, True, True, False, True]
    }
    df = pl.DataFrame(data).lazy()
    return df.group_by("category")


@pytest.fixture
def grouped_ibis_table() -> Any:
    """Ibis Table with group_by applied."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "C", "B", "A"],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8, 600.1],
        "active": [True, False, True, True, False, True]
    }
    tbl = DataFrameUtils.create_ibis(data)
    return tbl.group_by("category")


@pytest.fixture
def grouped_narwhals_df() -> Any:
    """Narwhals DataFrame with group_by applied."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "C", "B", "A"],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8, 600.1],
        "active": [True, False, True, True, False, True]
    }
    pandas_df = pd.DataFrame(data)
    nw_df = nw.from_native(pandas_df)
    return nw_df.group_by("category")


@pytest.fixture
def grouped_narwhals_lazyframe(sample_polars_lazyframe) -> Any:
    """Narwhals LazyFrame with group_by applied."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "C", "B", "A"],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8, 600.1],
        "active": [True, False, True, True, False, True]
    }
    polars_lazy_df = pl.DataFrame(data).lazy()
    nw_lazy = nw.from_native(polars_lazy_df)
    return nw_lazy.group_by("category")


@pytest.fixture
def all_grouped_backends():
    """All backend grouped DataFrames with identical data for testing."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "C", "B", "A"],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
        "value": [100.5, 200.7, 300.9, 400.2, 500.8, 600.1],
        "active": [True, False, True, True, False, True]
    }

    return {
        "pandas": pd.DataFrame(data).groupby("category"),
        "polars": pl.DataFrame(data).group_by("category"),
        "polars_lazy": pl.DataFrame(data).lazy().group_by("category"),
        "ibis": DataFrameUtils.create_ibis(data).group_by("category"),
        "narwhals": nw.from_native(pd.DataFrame(data)).group_by("category")
    }


# Window operation fixtures for testing reshape operations on windowed dataframes
@pytest.fixture
def windowed_pandas_rolling() -> Any:
    """Pandas DataFrame with rolling window applied (intermediate object)."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1],
        "amount": [100, 200, 300, 400, 500, 600]
    }
    df = pd.DataFrame(data)
    return df.rolling(window=3)


@pytest.fixture
def windowed_pandas_expanding() -> Any:
    """Pandas DataFrame with expanding window applied (intermediate object)."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1],
        "amount": [100, 200, 300, 400, 500, 600]
    }
    df = pd.DataFrame(data)
    return df.expanding()


@pytest.fixture
def windowed_pandas_ewm() -> Any:
    """Pandas DataFrame with exponentially weighted moving window applied."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1],
        "amount": [100, 200, 300, 400, 500, 600]
    }
    df = pd.DataFrame(data)
    return df.ewm(span=3)


@pytest.fixture
def windowed_pandas_groupby_rolling() -> Any:
    """Pandas GroupBy with rolling window applied (intermediate object)."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "B", "A", "B"],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1]
    }
    df = pd.DataFrame(data)
    return df.groupby("category").rolling(window=2)


@pytest.fixture
def windowed_polars_with_over() -> Any:
    """Polars DataFrame with window function applied - returns regular DataFrame."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "B", "A", "B"],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1]
    }
    df = pl.DataFrame(data)
    # Window operations in polars return regular DataFrames
    return df.with_columns([
        pl.col("value").sum().over("category").alias("sum_by_category")
    ])


@pytest.fixture
def windowed_polars_lazyframe_with_over() -> Any:
    """Polars LazyFrame with window function applied - returns LazyFrame."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "B", "A", "B"],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1]
    }
    df = pl.DataFrame(data).lazy()
    # Window operations in polars return LazyFrames
    return df.with_columns([
        pl.col("value").sum().over("category").alias("sum_by_category")
    ])


@pytest.fixture
def windowed_ibis_with_over() -> Any:
    """Ibis Table with computed column (simulates window result) - returns regular Table.

    Note: Full window function support varies by Ibis backend. This fixture
    creates a table with additional columns to simulate a windowed result,
    allowing us to test that reshape operations work on Ibis tables.
    """
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "B", "A", "B"],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1]
    }
    tbl = DataFrameUtils.create_ibis(data)
    # Add a computed column (simpler than full window function)
    return tbl.mutate(value_times_2=tbl.value * 2)


@pytest.fixture
def windowed_narwhals_with_over() -> Any:
    """Narwhals DataFrame with window function applied - returns regular DataFrame."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "category": ["A", "B", "A", "B", "A", "B"],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1]
    }
    pandas_df = pd.DataFrame(data)
    nw_df = nw.from_native(pandas_df)
    # Narwhals window operations (if supported) return regular DataFrames
    # For now, create a regular DataFrame as narwhals may not have full window support
    return nw_df


@pytest.fixture
def all_pandas_window_objects():
    """All pandas window intermediate objects for testing."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1],
        "amount": [100, 200, 300, 400, 500, 600]
    }
    df = pd.DataFrame(data)

    return {
        "rolling": df.rolling(window=3),
        "expanding": df.expanding(),
        "ewm": df.ewm(span=3)
    }


@pytest.fixture
def all_windowed_result_dataframes():
    """All backend DataFrames after window operations have been applied (materialized)."""
    data = {
        "id": [1, 2, 3, 4, 5, 6],
        "value": [10.5, 20.7, 30.9, 40.2, 50.8, 60.1],
        "amount": [100, 200, 300, 400, 500, 600]
    }

    # Pandas - apply window operation to get result DataFrame
    pdf = pd.DataFrame(data)
    pdf_windowed = pdf.rolling(window=3).sum()

    # Polars - window operations return regular DataFrames
    plf = pl.DataFrame(data)
    plf_windowed = plf.with_columns([
        pl.col("value").sum().over(pl.lit(1)).alias("value_sum")
    ])

    # Ibis - window operations return regular Tables
    ibis_tbl = DataFrameUtils.create_ibis(data)

    return {
        "pandas": pdf_windowed,
        "polars": plf_windowed,
        "ibis": ibis_tbl
    }
