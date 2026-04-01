"""
DataFrameUtils - High-level API for DataFrame operations.

This module provides a clean, user-facing API for DataFrame operations
using the DataFrameSystem architecture.

Architecture:
    DataFrameUtils delegates all operations to DataFrameSystem backends:
    - PolarsDataFrameSystem (native Polars)
    - NarwhalsDataFrameSystem (pandas, PyArrow, cuDF via Narwhals)
    - IbisDataFrameSystem (SQL backends via Ibis)

Usage:
    from mountainash_dataframes import DataFrameUtils

    # Cast operations
    pandas_df = DataFrameUtils.to_pandas(df)
    polars_df = DataFrameUtils.to_polars(df)

    # Introspection
    columns = DataFrameUtils.get_column_names(df)
    shape = DataFrameUtils.get_shape(df)

    # Selection
    selected = DataFrameUtils.select(df, ['col1', 'col2'])

    # Join
    joined = DataFrameUtils.join(left, right, on='key')

Note:
    Methods for Python data ingress/egress (create_*, to_list_of_*, etc.)
    have been moved to mountainash-pydata package.

    Methods for schema management have been moved to mountainash-schema package.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    import pandas as pd
    import polars as pl
    import pyarrow as pa
    import ibis.expr.types as ir

# Import DataFrameSystem infrastructure
from ..dataframe_system import DataFrameSystemFactory, DataFrameSystem

# Type alias for supported DataFrames
SupportedDataFrames = Any  # Will be properly typed when typing module is updated


class DataFrameUtils:
    """
    High-level API for DataFrame operations.

    All operations are delegated to backend-specific DataFrameSystems,
    which are automatically selected based on the input DataFrame type.

    Supported backends:
    - Polars (DataFrame and LazyFrame)
    - pandas (via Narwhals)
    - PyArrow (via Narwhals)
    - Ibis (SQL backends)
    """

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    @classmethod
    def _get_system(cls, df: SupportedDataFrames) -> DataFrameSystem:
        """Get the appropriate DataFrameSystem for the input DataFrame."""
        return DataFrameSystemFactory.get_system(df)

    # =========================================================================
    # Cast Operations (DataFrame -> DataFrame)
    # =========================================================================

    @classmethod
    def to_polars(
        cls,
        df: SupportedDataFrames,
        /,
        *,
        as_lazy: bool = False,
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """
        Convert DataFrame to Polars.

        Args:
            df: Input DataFrame (any supported type)
            as_lazy: If True, return LazyFrame instead of DataFrame

        Returns:
            Polars DataFrame or LazyFrame
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.to_polars(df, as_lazy=as_lazy)

    @classmethod
    def to_pandas(cls, df: SupportedDataFrames, /) -> "pd.DataFrame":
        """
        Convert DataFrame to pandas.

        Args:
            df: Input DataFrame (any supported type)

        Returns:
            pandas DataFrame
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.to_pandas(df)

    @classmethod
    def to_narwhals(
        cls,
        df: SupportedDataFrames,
        /,
        *,
        eager_only: bool = True,
    ) -> Any:
        """
        Convert DataFrame to Narwhals.

        Args:
            df: Input DataFrame (any supported type)
            eager_only: If True, only support eager DataFrames

        Returns:
            Narwhals DataFrame
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.to_narwhals(df, eager_only=eager_only)

    @classmethod
    def to_pyarrow(cls, df: SupportedDataFrames, /) -> "pa.Table":
        """
        Convert DataFrame to PyArrow Table.

        Args:
            df: Input DataFrame (any supported type)

        Returns:
            PyArrow Table
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.to_pyarrow(df)

    @classmethod
    def to_ibis(
        cls,
        df: SupportedDataFrames,
        /,
        *,
        backend: Optional[Any] = None,
        table_name: Optional[str] = None,
    ) -> "ir.Table":
        """
        Convert DataFrame to Ibis Table.

        Args:
            df: Input DataFrame (any supported type)
            backend: Ibis backend connection (default: in-memory DuckDB)
            table_name: Name for the table in the backend

        Returns:
            Ibis Table
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.to_ibis(df, backend=backend, table_name=table_name)

    # =========================================================================
    # Introspection Operations
    # =========================================================================

    @classmethod
    def get_shape(cls, df: SupportedDataFrames, /) -> Tuple[int, int]:
        """
        Get DataFrame shape as (rows, columns).

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (row_count, column_count)
        """
        if df is None:
            return (0, 0)
        system = cls._get_system(df)
        return system.get_shape(df)

    @classmethod
    def get_column_names(cls, df: SupportedDataFrames, /) -> List[str]:
        """
        Get list of column names.

        Args:
            df: Input DataFrame

        Returns:
            List of column names
        """
        if df is None:
            return []
        system = cls._get_system(df)
        return system.get_column_names(df)

    @classmethod
    def get_columns(cls, df: SupportedDataFrames, /) -> List[str]:
        """Alias for get_column_names."""
        return cls.get_column_names(df)

    @classmethod
    def column_names(cls, df: SupportedDataFrames, /) -> List[str]:
        """Alias for get_column_names (backward compatibility)."""
        return cls.get_column_names(df)

    @classmethod
    def get_schema(cls, df: SupportedDataFrames, /) -> Dict[str, Any]:
        """
        Get column names and their types.

        Args:
            df: Input DataFrame

        Returns:
            Dict mapping column names to type strings
        """
        if df is None:
            return {}
        system = cls._get_system(df)
        return system.get_schema(df)

    @classmethod
    def get_dtypes(cls, df: SupportedDataFrames, /) -> Dict[str, Any]:
        """
        Get column data types.

        Args:
            df: Input DataFrame

        Returns:
            Dict mapping column names to type objects
        """
        if df is None:
            return {}
        system = cls._get_system(df)
        return system.get_dtypes(df)

    # =========================================================================
    # Select Operations
    # =========================================================================

    @classmethod
    def select(
        cls,
        df: SupportedDataFrames,
        /,
        columns: Union[List[str], str],
    ) -> SupportedDataFrames:
        """
        Select columns from DataFrame.

        Args:
            df: Input DataFrame
            columns: Column name(s) to select

        Returns:
            DataFrame with selected columns
        """
        if df is None:
            return None
        if isinstance(columns, str):
            columns = [columns]
        system = cls._get_system(df)
        return system.select(df, columns)

    @classmethod
    def drop(
        cls,
        df: SupportedDataFrames,
        /,
        columns: Union[List[str], str],
    ) -> SupportedDataFrames:
        """
        Drop columns from DataFrame.

        Args:
            df: Input DataFrame
            columns: Column name(s) to drop

        Returns:
            DataFrame without dropped columns
        """
        if df is None:
            return None
        if isinstance(columns, str):
            columns = [columns]
        system = cls._get_system(df)
        return system.drop(df, columns)

    @classmethod
    def rename(
        cls,
        df: SupportedDataFrames,
        /,
        mapping: Dict[str, str],
    ) -> SupportedDataFrames:
        """
        Rename columns in DataFrame.

        Args:
            df: Input DataFrame
            mapping: Dict mapping old names to new names

        Returns:
            DataFrame with renamed columns
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.rename(df, mapping)

    @classmethod
    def reorder(
        cls,
        df: SupportedDataFrames,
        /,
        columns: List[str],
    ) -> SupportedDataFrames:
        """
        Reorder columns in DataFrame.

        Args:
            df: Input DataFrame
            columns: List of column names in desired order

        Returns:
            DataFrame with reordered columns
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.reorder(df, columns)

    # =========================================================================
    # Join Operations
    # =========================================================================

    @classmethod
    def join(
        cls,
        left: SupportedDataFrames,
        right: SupportedDataFrames,
        /,
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        how: str = "inner",
        suffix: str = "_right",
    ) -> SupportedDataFrames:
        """
        Join two DataFrames.

        Args:
            left: Left DataFrame
            right: Right DataFrame
            on: Column name to join on (if same in both)
            left_on: Column name in left DataFrame
            right_on: Column name in right DataFrame
            how: Join type ('inner', 'left', 'right', 'outer')
            suffix: Suffix for duplicate column names

        Returns:
            Joined DataFrame
        """
        if left is None or right is None:
            return None
        system = cls._get_system(left)
        return system.join(
            left, right,
            on=on, left_on=left_on, right_on=right_on,
            how=how, suffix=suffix
        )

    @classmethod
    def inner_join(
        cls,
        left: SupportedDataFrames,
        right: SupportedDataFrames,
        /,
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> SupportedDataFrames:
        """Inner join (convenience method)."""
        return cls.join(
            left, right,
            on=on, left_on=left_on, right_on=right_on,
            how="inner", suffix=suffix
        )

    @classmethod
    def left_join(
        cls,
        left: SupportedDataFrames,
        right: SupportedDataFrames,
        /,
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> SupportedDataFrames:
        """Left join (convenience method)."""
        return cls.join(
            left, right,
            on=on, left_on=left_on, right_on=right_on,
            how="left", suffix=suffix
        )

    @classmethod
    def outer_join(
        cls,
        left: SupportedDataFrames,
        right: SupportedDataFrames,
        /,
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> SupportedDataFrames:
        """Outer join (convenience method)."""
        return cls.join(
            left, right,
            on=on, left_on=left_on, right_on=right_on,
            how="outer", suffix=suffix
        )

    # =========================================================================
    # Filter Operations
    # =========================================================================

    @classmethod
    def filter(
        cls,
        df: SupportedDataFrames,
        /,
        expression: Any,
    ) -> SupportedDataFrames:
        """
        Filter DataFrame rows by expression.

        Args:
            df: Input DataFrame
            expression: Backend-specific filter expression

        Returns:
            Filtered DataFrame
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.filter(df, expression)

    # =========================================================================
    # Row Operations
    # =========================================================================

    @classmethod
    def head(cls, df: SupportedDataFrames, /, n: int = 5) -> SupportedDataFrames:
        """
        Get first n rows.

        Args:
            df: Input DataFrame
            n: Number of rows (default: 5)

        Returns:
            DataFrame with first n rows
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.head(df, n)

    @classmethod
    def tail(cls, df: SupportedDataFrames, /, n: int = 5) -> SupportedDataFrames:
        """
        Get last n rows.

        Args:
            df: Input DataFrame
            n: Number of rows (default: 5)

        Returns:
            DataFrame with last n rows
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.tail(df, n)

    @classmethod
    def sample(cls, df: SupportedDataFrames, /, n: int = 5) -> SupportedDataFrames:
        """
        Get random sample of n rows.

        Args:
            df: Input DataFrame
            n: Number of rows (default: 5)

        Returns:
            DataFrame with random n rows
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.sample(df, n)

    @classmethod
    def count(cls, df: SupportedDataFrames, /) -> int:
        """
        Get row count.

        Args:
            df: Input DataFrame

        Returns:
            Number of rows
        """
        if df is None:
            return 0
        shape = cls.get_shape(df)
        return shape[0]

    # =========================================================================
    # Lazy/Eager Operations
    # =========================================================================

    @classmethod
    def is_lazy(cls, df: SupportedDataFrames, /) -> bool:
        """
        Check if DataFrame is lazy (deferred execution).

        Args:
            df: Input DataFrame

        Returns:
            True if lazy, False if eager
        """
        if df is None:
            return False
        system = cls._get_system(df)
        return system.is_lazy(df)

    @classmethod
    def collect(cls, df: SupportedDataFrames, /) -> SupportedDataFrames:
        """
        Collect lazy DataFrame to eager.

        Args:
            df: Input DataFrame (lazy or eager)

        Returns:
            Eager DataFrame
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.collect(df)

    @classmethod
    def lazy(cls, df: SupportedDataFrames, /) -> SupportedDataFrames:
        """
        Convert eager DataFrame to lazy (if supported).

        Args:
            df: Input DataFrame

        Returns:
            Lazy DataFrame (or original if not supported)
        """
        if df is None:
            return None
        system = cls._get_system(df)
        return system.lazy(df)


# =============================================================================
# COMMENTED OUT: Methods requiring ingress/egress (belong to mountainash-pydata)
# =============================================================================

# These methods have been moved to the mountainash-pydata package:
#
# DataFrame Creation (Python data -> DataFrame):
#   - create_dataframe()
#   - create_pandas()
#   - create_polars()
#   - create_pyarrow()
#   - create_ibis()
#
# DataFrame to Python Data:
#   - to_dictionary_of_lists()
#   - to_dictionary_of_series_pandas()
#   - to_dictionary_of_series_polars()
#   - to_list_of_dictionaries()
#   - to_list_of_tuples()
#   - to_list_of_named_tuples()
#   - to_list_of_typed_named_tuples()
#   - to_index_of_dictionaries()
#   - to_index_of_tuples()
#   - to_index_of_named_tuples()
#   - to_index_of_typed_named_tuples()
#   - to_list_of_dataclasses()
#   - to_list_of_pydantic()
#   - get_column_as_list()
#   - get_column_as_series_pandas()
#   - get_column_as_series_polars()
#   - get_column_as_set()
#   - get_first_row_as_dict()


# =============================================================================
# COMMENTED OUT: Methods requiring schema (belong to mountainash-schema)
# =============================================================================

# These methods have been moved to the mountainash-schema package:
#
# Schema Operations:
#   - table_schema_ibis()
#   - cast_dataframe() with column_config
#   - Any method with SchemaConfig parameter


# =============================================================================
# COMMENTED OUT: Methods requiring additional refactoring
# =============================================================================

# These methods need additional work to use DataFrameSystem:
#
# Batch Operations:
#   - split_dataframe_in_batches()
#   - split_dataframe_in_batches_generator()
#
# Complex Operations:
#   - distinct()  # Needs to be added to DataFrameSystem
#   - get_dataframe_info()  # Needs to be added to DataFrameSystem


# =============================================================================
# Module-level convenience functions
# =============================================================================

def to_polars(df: SupportedDataFrames, /, *, as_lazy: bool = False) -> Any:
    """Convert DataFrame to Polars."""
    return DataFrameUtils.to_polars(df, as_lazy=as_lazy)

def to_pandas(df: SupportedDataFrames, /) -> Any:
    """Convert DataFrame to pandas."""
    return DataFrameUtils.to_pandas(df)

def to_narwhals(df: SupportedDataFrames, /, *, eager_only: bool = True) -> Any:
    """Convert DataFrame to Narwhals."""
    return DataFrameUtils.to_narwhals(df, eager_only=eager_only)

def to_pyarrow(df: SupportedDataFrames, /) -> Any:
    """Convert DataFrame to PyArrow."""
    return DataFrameUtils.to_pyarrow(df)

def to_ibis(df: SupportedDataFrames, /, *, backend: Any = None, table_name: str = None) -> Any:
    """Convert DataFrame to Ibis."""
    return DataFrameUtils.to_ibis(df, backend=backend, table_name=table_name)

def get_shape(df: SupportedDataFrames, /) -> Tuple[int, int]:
    """Get DataFrame shape."""
    return DataFrameUtils.get_shape(df)

def get_column_names(df: SupportedDataFrames, /) -> List[str]:
    """Get column names."""
    return DataFrameUtils.get_column_names(df)

def column_names(df: SupportedDataFrames, /) -> List[str]:
    """Get column names (alias)."""
    return DataFrameUtils.get_column_names(df)

def get_schema(df: SupportedDataFrames, /) -> Dict[str, Any]:
    """Get DataFrame schema."""
    return DataFrameUtils.get_schema(df)

def select(df: SupportedDataFrames, /, columns: Union[List[str], str]) -> SupportedDataFrames:
    """Select columns."""
    return DataFrameUtils.select(df, columns)

def drop(df: SupportedDataFrames, /, columns: Union[List[str], str]) -> SupportedDataFrames:
    """Drop columns."""
    return DataFrameUtils.drop(df, columns)

def rename(df: SupportedDataFrames, /, mapping: Dict[str, str]) -> SupportedDataFrames:
    """Rename columns."""
    return DataFrameUtils.rename(df, mapping)

def join(
    left: SupportedDataFrames,
    right: SupportedDataFrames,
    /,
    *,
    on: str = None,
    left_on: str = None,
    right_on: str = None,
    how: str = "inner",
) -> SupportedDataFrames:
    """Join DataFrames."""
    return DataFrameUtils.join(left, right, on=on, left_on=left_on, right_on=right_on, how=how)

def filter(df: SupportedDataFrames, /, expression: Any) -> SupportedDataFrames:
    """Filter DataFrame."""
    return DataFrameUtils.filter(df, expression)

def head(df: SupportedDataFrames, /, n: int = 5) -> SupportedDataFrames:
    """Get first n rows."""
    return DataFrameUtils.head(df, n)

def tail(df: SupportedDataFrames, /, n: int = 5) -> SupportedDataFrames:
    """Get last n rows."""
    return DataFrameUtils.tail(df, n)

def count(df: SupportedDataFrames, /) -> int:
    """Get row count."""
    return DataFrameUtils.count(df)

def is_lazy(df: SupportedDataFrames, /) -> bool:
    """Check if lazy."""
    return DataFrameUtils.is_lazy(df)

def collect(df: SupportedDataFrames, /) -> SupportedDataFrames:
    """Collect lazy to eager."""
    return DataFrameUtils.collect(df)
