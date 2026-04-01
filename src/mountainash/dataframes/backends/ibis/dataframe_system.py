"""
IbisDataFrameSystem - DataFrameSystem implementation for SQL backends via Ibis.

Supports DuckDB, PostgreSQL, BigQuery, Snowflake, and other Ibis backends.
Operations are deferred until explicitly collected.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from ...core.dataframe_system.base import DataFrameSystem
from ...core.dataframe_system.constants import CONST_DATAFRAME_BACKEND
from ...core.dataframe_system.factory import register_dataframe_system

if TYPE_CHECKING:
    import pandas as pd
    import pyarrow as pa
    import ibis.expr.types as ir

logger = logging.getLogger(__name__)


def _import_ibis():
    """Lazy import of ibis."""
    import ibis

    return ibis


def _import_polars():
    """Lazy import of polars."""
    import polars as pl

    return pl


@register_dataframe_system(CONST_DATAFRAME_BACKEND.IBIS)
class IbisDataFrameSystem(DataFrameSystem):
    """
    DataFrameSystem implementation for Ibis (SQL backends).

    Provides SQL backend support for:
    - DuckDB (default in-memory backend)
    - PostgreSQL
    - BigQuery
    - Snowflake
    - MySQL, SQLite, and other Ibis backends

    Operations are deferred (lazy) until explicitly executed.
    """

    # =========================================================================
    # Backend Identification
    # =========================================================================

    @property
    def backend_type(self) -> CONST_DATAFRAME_BACKEND:
        return CONST_DATAFRAME_BACKEND.IBIS

    def is_native_type(self, obj: Any) -> bool:
        """Check if object is an Ibis Table or expression."""
        ibis = _import_ibis()
        return isinstance(obj, ibis.expr.types.Table)

    # =========================================================================
    # Cast Operations
    # =========================================================================

    def to_polars(self, table: "ir.Table", *, as_lazy: bool = False) -> Any:
        """Convert Ibis Table to Polars DataFrame."""
        pl = _import_polars()

        # Execute and convert to PyArrow, then to Polars
        arrow_table = table.to_pyarrow()
        polars_df = pl.from_arrow(arrow_table)

        if as_lazy:
            return polars_df.lazy()
        return polars_df

    def to_pandas(self, table: "ir.Table") -> "pd.DataFrame":
        """Convert Ibis Table to pandas DataFrame."""
        return table.to_pandas()

    def to_narwhals(self, table: "ir.Table", *, eager_only: bool = True) -> Any:
        """Convert Ibis Table to Narwhals DataFrame."""
        import narwhals as nw

        # Execute to Polars first
        polars_df = self.to_polars(table, as_lazy=False)
        return nw.from_native(polars_df, eager_only=eager_only)

    def to_ibis(
        self,
        table: "ir.Table",
        *,
        backend: Optional[Any] = None,
        table_name: Optional[str] = None,
    ) -> "ir.Table":
        """Return Ibis Table (native - potentially transfer to new backend)."""
        if backend is None:
            return table

        # Transfer to new backend
        arrow_table = table.to_pyarrow()
        name = table_name or "transferred_table"
        return backend.create_table(name, arrow_table, overwrite=True)

    def to_pyarrow(self, table: "ir.Table") -> "pa.Table":
        """Convert Ibis Table to PyArrow Table."""
        return table.to_pyarrow()

    # =========================================================================
    # Introspect Operations
    # =========================================================================

    def get_shape(self, table: "ir.Table") -> Tuple[int, int]:
        """Get (rows, columns) shape."""
        # Column count from schema
        col_count = len(table.columns)

        # Row count requires execution
        row_count = table.count().execute()

        return (row_count, col_count)

    def get_column_names(self, table: "ir.Table") -> List[str]:
        """Get list of column names."""
        return list(table.columns)

    def get_columns(self, table: "ir.Table") -> List[str]:
        """Alias for get_column_names."""
        return self.get_column_names(table)

    def get_schema(self, table: "ir.Table") -> Dict[str, Any]:
        """Get column names and their types."""
        schema = table.schema()
        return {name: str(dtype) for name, dtype in schema.items()}

    def get_dtypes(self, table: "ir.Table") -> Dict[str, Any]:
        """Get column data types."""
        schema = table.schema()
        return dict(schema)

    # =========================================================================
    # Select Operations
    # =========================================================================

    def select(self, table: "ir.Table", columns: List[str]) -> "ir.Table":
        """Select columns from Table."""
        return table.select(columns)

    def rename(self, table: "ir.Table", mapping: Dict[str, str]) -> "ir.Table":
        """Rename columns in Table."""
        return table.rename(mapping)

    def reorder(self, table: "ir.Table", columns: List[str]) -> "ir.Table":
        """Reorder columns in Table."""
        return table.select(columns)

    def drop(self, table: "ir.Table", columns: List[str]) -> "ir.Table":
        """Drop columns from Table."""
        return table.drop(columns)

    # =========================================================================
    # Join Operations
    # =========================================================================

    def join(
        self,
        left: "ir.Table",
        right: "ir.Table",
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        how: str = "inner",
        suffix: str = "_right",
    ) -> "ir.Table":
        """Join two Tables."""
        # Map join types to Ibis
        ibis_how = how
        if how == "outer":
            ibis_how = "outer"

        if on is not None:
            # Same column name in both tables
            predicates = left[on] == right[on]
        else:
            # Different column names
            predicates = left[left_on] == right[right_on]

        return left.join(right, predicates, how=ibis_how, suffixes=("", suffix))

    # =========================================================================
    # Filter Operations
    # =========================================================================

    def filter(self, table: "ir.Table", expression: Any) -> "ir.Table":
        """Filter Table by expression."""
        return table.filter(expression)

    # =========================================================================
    # Row Operations
    # =========================================================================

    def head(self, table: "ir.Table", n: int = 5) -> "ir.Table":
        """Get first n rows."""
        return table.head(n)

    def tail(self, table: "ir.Table", n: int = 5) -> "ir.Table":
        """Get last n rows (requires execution for some backends)."""
        # Ibis doesn't have native tail - need to use offset
        # This is expensive as it requires knowing row count
        total_rows = table.count().execute()
        offset = max(0, total_rows - n)
        return table.limit(n, offset=offset)

    def sample(self, table: "ir.Table", n: int = 5) -> "ir.Table":
        """Get random sample of n rows."""
        ibis = _import_ibis()

        # Ibis sample takes a fraction, not count
        # We need to estimate fraction or use TABLESAMPLE if available
        total_rows = table.count().execute()
        if total_rows == 0:
            return table

        fraction = min(1.0, n / total_rows)

        # Use sample if available, otherwise random ordering with limit
        if hasattr(table, "sample"):
            return table.sample(fraction).head(n)
        else:
            return table.order_by(ibis.random()).head(n)

    # =========================================================================
    # Lazy/Eager Operations
    # =========================================================================

    def is_lazy(self, table: "ir.Table") -> bool:
        """Ibis Tables are always lazy (deferred execution)."""
        return True

    def collect(self, table: "ir.Table") -> "pd.DataFrame":
        """Execute and collect Ibis Table to pandas DataFrame."""
        return table.to_pandas()

    def lazy(self, table: "ir.Table") -> "ir.Table":
        """Return Table as-is (already lazy)."""
        return table
