"""
PolarsDataFrameSystem - Complete DataFrameSystem implementation for Polars.

Handles both eager DataFrames and lazy LazyFrames natively.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from ...core.dataframe_system.base import DataFrameSystem
from ...core.dataframe_system.constants import CONST_DATAFRAME_BACKEND
from ...core.dataframe_system.factory import register_dataframe_system

if TYPE_CHECKING:
    import polars as pl
    import pandas as pd
    import pyarrow as pa
    import ibis.expr.types as ir

logger = logging.getLogger(__name__)


def _import_polars():
    """Lazy import of polars."""
    import polars as pl

    return pl


def _import_narwhals():
    """Lazy import of narwhals."""
    import narwhals as nw

    return nw


def _import_pyarrow():
    """Lazy import of pyarrow."""
    import pyarrow as pa

    return pa


@register_dataframe_system(CONST_DATAFRAME_BACKEND.POLARS)
class PolarsDataFrameSystem(DataFrameSystem):
    """
    DataFrameSystem implementation for Polars.

    Provides native Polars operations for both DataFrame and LazyFrame.
    This is the primary backend with full feature support.
    """

    # =========================================================================
    # Backend Identification
    # =========================================================================

    @property
    def backend_type(self) -> CONST_DATAFRAME_BACKEND:
        return CONST_DATAFRAME_BACKEND.POLARS

    def is_native_type(self, obj: Any) -> bool:
        """Check if object is a Polars DataFrame or LazyFrame."""
        pl = _import_polars()
        return isinstance(obj, (pl.DataFrame, pl.LazyFrame))

    # =========================================================================
    # Cast Operations
    # =========================================================================

    def to_polars(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], *, as_lazy: bool = False
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Return Polars DataFrame/LazyFrame (native - minimal conversion)."""
        pl = _import_polars()

        if as_lazy:
            if isinstance(df, pl.LazyFrame):
                return df
            return df.lazy()
        else:
            if isinstance(df, pl.DataFrame):
                return df
            return df.collect()

    def to_pandas(self, df: Union["pl.DataFrame", "pl.LazyFrame"]) -> "pd.DataFrame":
        """Convert Polars to pandas DataFrame."""
        pl = _import_polars()

        if isinstance(df, pl.LazyFrame):
            df = df.collect()
        return df.to_pandas()

    def to_narwhals(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], *, eager_only: bool = True
    ) -> Any:
        """Wrap Polars DataFrame in Narwhals."""
        nw = _import_narwhals()

        if eager_only:
            pl = _import_polars()
            if isinstance(df, pl.LazyFrame):
                df = df.collect()
        return nw.from_native(df)

    def to_ibis(
        self,
        df: Union["pl.DataFrame", "pl.LazyFrame"],
        *,
        backend: Optional[Any] = None,
        table_name: Optional[str] = None,
    ) -> "ir.Table":
        """Convert Polars DataFrame to Ibis Table."""
        import ibis

        pl = _import_polars()

        # Collect if lazy
        if isinstance(df, pl.LazyFrame):
            df = df.collect()

        # Convert to PyArrow for Ibis compatibility
        arrow_table = df.to_arrow()

        # Use provided backend or create in-memory DuckDB
        if backend is None:
            backend = ibis.duckdb.connect()

        # Register table with backend
        name = table_name or "temp_table"
        return backend.create_table(name, arrow_table, overwrite=True)

    def to_pyarrow(self, df: Union["pl.DataFrame", "pl.LazyFrame"]) -> "pa.Table":
        """Convert Polars DataFrame to PyArrow Table."""
        pl = _import_polars()

        if isinstance(df, pl.LazyFrame):
            df = df.collect()
        return df.to_arrow()

    # =========================================================================
    # Introspect Operations
    # =========================================================================

    def get_shape(self, df: Union["pl.DataFrame", "pl.LazyFrame"]) -> Tuple[int, int]:
        """Get (rows, columns) shape."""
        pl = _import_polars()

        if isinstance(df, pl.LazyFrame):
            # For LazyFrame, we need to collect to get row count
            # Or use schema for columns only
            schema = df.collect_schema()
            # Row count requires collection for LazyFrame
            collected = df.collect()
            return (collected.height, len(schema))
        return df.shape

    def get_column_names(self, df: Union["pl.DataFrame", "pl.LazyFrame"]) -> List[str]:
        """Get list of column names."""
        pl = _import_polars()

        if isinstance(df, pl.LazyFrame):
            return df.collect_schema().names()
        return df.columns

    def get_columns(self, df: Union["pl.DataFrame", "pl.LazyFrame"]) -> List[str]:
        """Alias for get_column_names."""
        return self.get_column_names(df)

    def get_schema(self, df: Union["pl.DataFrame", "pl.LazyFrame"]) -> Dict[str, Any]:
        """Get column names and their types."""
        pl = _import_polars()

        if isinstance(df, pl.LazyFrame):
            schema = df.collect_schema()
            return {name: str(dtype) for name, dtype in schema.items()}
        return {name: str(dtype) for name, dtype in df.schema.items()}

    def get_dtypes(self, df: Union["pl.DataFrame", "pl.LazyFrame"]) -> Dict[str, Any]:
        """Get column data types."""
        pl = _import_polars()

        if isinstance(df, pl.LazyFrame):
            schema = df.collect_schema()
            return dict(schema)
        return dict(df.schema)

    # =========================================================================
    # Select Operations
    # =========================================================================

    def select(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], columns: List[str]
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Select columns from DataFrame."""
        return df.select(columns)

    def rename(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], mapping: Dict[str, str]
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Rename columns in DataFrame."""
        return df.rename(mapping)

    def reorder(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], columns: List[str]
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Reorder columns in DataFrame."""
        return df.select(columns)

    def drop(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], columns: List[str]
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Drop columns from DataFrame."""
        return df.drop(columns)

    # =========================================================================
    # Join Operations
    # =========================================================================

    def join(
        self,
        left: Union["pl.DataFrame", "pl.LazyFrame"],
        right: Union["pl.DataFrame", "pl.LazyFrame"],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        how: str = "inner",
        suffix: str = "_right",
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Join two DataFrames."""
        # Polars join API
        if on is not None:
            return left.join(right, on=on, how=how, suffix=suffix)
        else:
            return left.join(
                right, left_on=left_on, right_on=right_on, how=how, suffix=suffix
            )

    # =========================================================================
    # Filter Operations
    # =========================================================================

    def filter(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], expression: Any
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Filter DataFrame by expression."""
        return df.filter(expression)

    # =========================================================================
    # Row Operations
    # =========================================================================

    def head(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], n: int = 5
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Get first n rows."""
        return df.head(n)

    def tail(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], n: int = 5
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Get last n rows."""
        return df.tail(n)

    def sample(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"], n: int = 5
    ) -> Union["pl.DataFrame", "pl.LazyFrame"]:
        """Get random sample of n rows."""
        pl = _import_polars()

        if isinstance(df, pl.LazyFrame):
            # LazyFrame doesn't support sample directly
            return df.collect().sample(n).lazy()
        return df.sample(n)

    # =========================================================================
    # Lazy/Eager Operations
    # =========================================================================

    def is_lazy(self, df: Union["pl.DataFrame", "pl.LazyFrame"]) -> bool:
        """Check if DataFrame is lazy."""
        pl = _import_polars()
        return isinstance(df, pl.LazyFrame)

    def collect(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"]
    ) -> "pl.DataFrame":
        """Collect lazy DataFrame to eager."""
        pl = _import_polars()

        if isinstance(df, pl.LazyFrame):
            return df.collect()
        return df

    def lazy(
        self, df: Union["pl.DataFrame", "pl.LazyFrame"]
    ) -> "pl.LazyFrame":
        """Convert eager DataFrame to lazy."""
        pl = _import_polars()

        if isinstance(df, pl.DataFrame):
            return df.lazy()
        return df
