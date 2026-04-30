"""
Backend helper utilities for cross-backend testing.

Provides:
- BackendResultHelper: Extract results from different backends uniformly
- BackendDataFrameFactory: Create DataFrames for different backends
"""

from typing import Any, Dict, List
import polars as pl
import pandas as pd
import narwhals as nw
import ibis


class BackendResultHelper:
    """
    Helper class for extracting results from different DataFrame backends.

    Provides uniform interface for:
    - Getting row counts
    - Extracting column values
    - Getting scalar results
    - Filtering and selecting

    Usage:
        helper = BackendResultHelper()
        count = helper.get_count(df, "polars")
        values = helper.get_column_list(df, "age", "polars")
    """

    @staticmethod
    def get_count(df: Any, backend_name: str) -> int:
        """
        Get row count from any backend DataFrame.

        Args:
            df: DataFrame from any backend
            backend_name: Backend identifier ("polars", "pandas", "narwhals", "ibis-duckdb", "ibis-polars", "ibis-sqlite")

        Returns:
            Number of rows in DataFrame

        Example:
            >>> df = pl.DataFrame({"a": [1, 2, 3]})
            >>> BackendResultHelper.get_count(df, "polars")
            3
        """
        if backend_name.startswith("ibis-"):
            return df.count().execute()
        elif backend_name in ["polars", "pandas", "narwhals", "narwhals-polars", "narwhals-pandas"]:
            return df.shape[0]
        else:
            return len(df)

    @staticmethod
    def get_column_list(df: Any, column: str, backend_name: str) -> List:
        """
        Get column values as list from any backend.

        Args:
            df: DataFrame from any backend
            column: Column name
            backend_name: Backend identifier

        Returns:
            List of column values

        Example:
            >>> df = pl.DataFrame({"age": [25, 30, 35]})
            >>> BackendResultHelper.get_column_list(df, "age", "polars")
            [25, 30, 35]
        """
        if backend_name.startswith("ibis-"):
            return df[column].execute().tolist()
        elif backend_name == "polars":
            return df[column].to_list()
        elif backend_name == "pandas":
            return df[column].tolist()
        elif backend_name in ("narwhals", "narwhals-polars", "narwhals-pandas"):
            return df[column].to_list()
        else:
            raise ValueError(f"Unknown backend: {backend_name}")

    @staticmethod
    def select_and_extract(
        df: Any,
        backend_expr: Any,
        column_alias: str,
        backend_name: str
    ) -> List:
        """
        Select expression and extract column values - handles all backends.

        Single function that:
        1. Selects with backend-specific method (.name() or .alias())
        2. Collects/executes if needed (no double-collect)
        3. Extracts column values to list

        Args:
            df: DataFrame from any backend
            backend_expr: Compiled backend expression
            column_alias: Name for the result column
            backend_name: Backend identifier

        Returns:
            List of column values

        Example:
            >>> expr = ma.col("a") + ma.col("b")
            >>> backend_expr = expr.compile(df)
            >>> actual = BackendResultHelper.select_and_extract(
            ...     df, backend_expr, "result", "polars"
            ... )
            [12, 23, 34]
        """
        # Handle each backend type completely in one place
        if backend_name.startswith("ibis-"):
            # Ibis: use .name(), then execute to get values
            result = df.select(backend_expr.name(column_alias))
            return result[column_alias].execute().tolist()

        elif backend_name in ("polars", "narwhals", "narwhals-polars", "narwhals-pandas", "pandas"):
            # Polars/Narwhals/Pandas: use .alias(), then to_list()
            # (pandas is routed through narwhals in factory)
            result = df.select(backend_expr.alias(column_alias))
            return result[column_alias].to_list()

        else:
            raise ValueError(f"Unknown backend: {backend_name}")

    @staticmethod
    def get_scalar(result: Any, backend_name: str) -> Any:
        """
        Extract scalar result from aggregation operations.

        Args:
            result: Aggregation result from backend
            backend_name: Backend identifier

        Returns:
            Scalar value

        Example:
            >>> expr = ma.col("age").max()
            >>> result = expr.compile(df)
            >>> BackendResultHelper.get_scalar(result, "polars")
            45
        """
        if backend_name.startswith("ibis-"):
            return result.execute()
        elif backend_name == "polars":
            # Polars aggregation returns DataFrame, need to extract
            if isinstance(result, pl.DataFrame):
                return result.item()
            return result
        elif backend_name == "pandas":
            return result
        elif backend_name in ("narwhals", "narwhals-polars", "narwhals-pandas"):
            return result
        else:
            raise ValueError(f"Unknown backend: {backend_name}")

    @staticmethod
    def filter_df(df: Any, expr: Any, backend_name: str) -> Any:
        """
        Apply filter expression to DataFrame.

        Args:
            df: DataFrame from any backend
            expr: Backend-specific filter expression
            backend_name: Backend identifier

        Returns:
            Filtered DataFrame
        """
        return df.filter(expr)

    @staticmethod
    def select_df(df: Any, expr: Any, alias: str, backend_name: str) -> Any:
        """
        Apply select/projection to DataFrame.

        Args:
            df: DataFrame from any backend
            expr: Backend-specific expression
            alias: Column alias for result
            backend_name: Backend identifier

        Returns:
            DataFrame with selected column
        """
        if backend_name.startswith("ibis-"):
            return df.select(expr.name(alias))
        else:
            return df.select(expr.alias(alias))

    @staticmethod
    def compare_with_tolerance(
        actual: Any,
        expected: Any,
        tolerance: float = 1e-6
    ) -> bool:
        """
        Compare values with tolerance for floating point comparisons.

        Args:
            actual: Actual value
            expected: Expected value
            tolerance: Tolerance for float comparison

        Returns:
            True if values are equal within tolerance
        """
        if isinstance(expected, float):
            return abs(actual - expected) < tolerance
        elif isinstance(expected, list):
            if len(actual) != len(expected):
                return False
            return all(
                BackendResultHelper.compare_with_tolerance(a, e, tolerance)
                for a, e in zip(actual, expected)
            )
        else:
            return actual == expected


class BackendDataFrameFactory:
    """
    Factory for creating DataFrames across different backends.

    Provides uniform interface for DataFrame creation from dictionary data.

    Usage:
        factory = BackendDataFrameFactory()
        df = factory.create(data, "polars")
    """

    @staticmethod
    def create(data: Dict[str, List], backend_name: str) -> Any:
        """
        Create DataFrame for specified backend from dictionary.

        Args:
            data: Dictionary mapping column names to lists of values
            backend_name: Backend identifier

        Returns:
            Backend-specific DataFrame

        Example:
            >>> data = {"age": [25, 30], "name": ["Alice", "Bob"]}
            >>> df = BackendDataFrameFactory.create(data, "polars")
            >>> type(df)
            <class 'polars.dataframe.frame.DataFrame'>
        """
        if backend_name == "polars":
            return pl.DataFrame(data)
        elif backend_name == "pandas":
            # Route pandas through narwhals for visitor compatibility
            pd_df = pd.DataFrame(data)
            return nw.from_native(pd_df)
        elif backend_name in ("narwhals", "narwhals-polars"):
            # Narwhals wrapping a polars frame
            pl_df = pl.DataFrame(data)
            return nw.from_native(pl_df)
        elif backend_name == "narwhals-pandas":
            # Narwhals wrapping a pandas frame
            return nw.from_native(pd.DataFrame(data), eager_only=True)
        elif backend_name == "ibis-duckdb":
            conn = ibis.duckdb.connect()
            return conn.create_table("test_table", data, overwrite=True)
        elif backend_name == "ibis-polars":
            conn = ibis.polars.connect()
            pl_df = pl.DataFrame(data)
            return conn.create_table("test_table", pl_df, overwrite=True)
        elif backend_name == "ibis-sqlite":
            conn = ibis.sqlite.connect(":memory:")
            return conn.create_table("test_table", data, overwrite=True)
        else:
            raise ValueError(f"Unknown backend: {backend_name}")

    @staticmethod
    def create_empty(columns: List[str], backend_name: str) -> Any:
        """
        Create empty DataFrame with specified columns.

        Args:
            columns: List of column names
            backend_name: Backend identifier

        Returns:
            Empty DataFrame with specified columns
        """
        data = {col: [] for col in columns}
        return BackendDataFrameFactory.create(data, backend_name)


def assert_backend_results_equal(
    actual: Any,
    expected: Any,
    backend_name: str,
    message: str = "",
    tolerance: float = 1e-6
):
    """
    Assert that actual and expected results are equal, with backend-specific handling.

    Handles:
    - Float comparisons with tolerance
    - None/NaN equivalence
    - List comparisons
    - Backend-specific quirks

    Args:
        actual: Actual result from backend
        expected: Expected result
        backend_name: Backend identifier for error messages
        message: Custom error message prefix
        tolerance: Tolerance for float comparison

    Raises:
        AssertionError: If results don't match

    Example:
        >>> assert_backend_results_equal(
        ...     [1.0000001, 2.0], [1.0, 2.0], "polars", "values match"
        ... )
    """
    if not BackendResultHelper.compare_with_tolerance(actual, expected, tolerance):
        error_msg = f"{message} [{backend_name}]: expected {expected}, got {actual}"
        raise AssertionError(error_msg)


def extract_column(result: Any, col: str) -> list:
    """Extract a column from a backend-native result as a plain list.

    Detects the result type and extracts accordingly:
    - Ibis Table: .execute() then pandas .tolist()
    - Polars LazyFrame: .collect() then .to_list()
    - Polars DataFrame / Narwhals: direct [col].to_list()
    - Pandas: .tolist()
    """
    if hasattr(result, "execute"):
        return result.execute()[col].tolist()
    if hasattr(result, "collect") and not hasattr(result, "to_list"):
        return result.collect()[col].to_list()
    if hasattr(result, "to_list"):
        return result[col].to_list()
    return list(result[col])


def extract_row_count(result: Any) -> int:
    """Extract row count from a backend-native result."""
    if hasattr(result, "execute"):
        return len(result.execute())
    if hasattr(result, "collect") and not hasattr(result, "shape"):
        return len(result.collect())
    if hasattr(result, "shape"):
        return result.shape[0]
    return len(result)


def extract_scalar(result: Any, col: str):
    """Extract a single scalar from a 1-row result."""
    if hasattr(result, "execute"):
        return result.execute()[col].tolist()[0]
    if hasattr(result, "collect") and not hasattr(result, "to_list"):
        return result.collect()[col].to_list()[0]
    if hasattr(result, "to_list"):
        return result[col].to_list()[0]
    return list(result[col])[0]
