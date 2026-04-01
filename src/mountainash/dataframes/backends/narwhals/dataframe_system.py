"""
NarwhalsDataFrameSystem - Universal adapter for pandas, PyArrow, cuDF via Narwhals.

This backend handles any DataFrame type that Narwhals can wrap, providing a
consistent interface across different backends.
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


def _import_narwhals():
    """Lazy import of narwhals."""
    import narwhals as nw

    return nw


def _import_polars():
    """Lazy import of polars."""
    import polars as pl

    return pl


@register_dataframe_system(CONST_DATAFRAME_BACKEND.NARWHALS)
class NarwhalsDataFrameSystem(DataFrameSystem):
    """
    DataFrameSystem implementation via Narwhals.

    This is the universal adapter that handles:
    - pandas DataFrames
    - PyArrow Tables
    - cuDF DataFrames
    - Native Narwhals DataFrames

    All operations are performed through the Narwhals abstraction layer.
    """

    # =========================================================================
    # Backend Identification
    # =========================================================================

    @property
    def backend_type(self) -> CONST_DATAFRAME_BACKEND:
        return CONST_DATAFRAME_BACKEND.NARWHALS

    def is_native_type(self, obj: Any) -> bool:
        """Check if object is a Narwhals-compatible type."""
        nw = _import_narwhals()

        # Check if it's already a Narwhals DataFrame
        if hasattr(nw, "DataFrame") and isinstance(obj, nw.DataFrame):
            return True

        # Check if it can be wrapped by Narwhals
        try:
            nw.from_native(obj, eager_only=True)
            return True
        except (TypeError, ValueError):
            return False

    def _wrap(self, df: Any) -> Any:
        """Wrap DataFrame in Narwhals if not already wrapped."""
        nw = _import_narwhals()

        # If already Narwhals, return as-is
        if hasattr(df, "_compliant_frame"):  # Narwhals internal attribute
            return df

        return nw.from_native(df, eager_only=True)

    def _unwrap(self, df: Any) -> Any:
        """Unwrap Narwhals DataFrame to native type."""
        nw = _import_narwhals()
        return nw.to_native(df)

    # =========================================================================
    # Cast Operations
    # =========================================================================

    def to_polars(self, df: Any, *, as_lazy: bool = False) -> Any:
        """Convert to Polars DataFrame via Narwhals."""
        nw = _import_narwhals()
        pl = _import_polars()

        wrapped = self._wrap(df)

        # Convert to Polars
        polars_df = wrapped.to_polars()

        if as_lazy:
            return polars_df.lazy()
        return polars_df

    def to_pandas(self, df: Any) -> "pd.DataFrame":
        """Convert to pandas DataFrame via Narwhals."""
        wrapped = self._wrap(df)
        return wrapped.to_pandas()

    def to_narwhals(self, df: Any, *, eager_only: bool = True) -> Any:
        """Wrap in Narwhals (or return if already wrapped)."""
        return self._wrap(df)

    def to_ibis(
        self,
        df: Any,
        *,
        backend: Optional[Any] = None,
        table_name: Optional[str] = None,
    ) -> "ir.Table":
        """Convert to Ibis Table via PyArrow."""
        import ibis

        # First convert to PyArrow
        arrow_table = self.to_pyarrow(df)

        # Use provided backend or create in-memory DuckDB
        if backend is None:
            backend = ibis.duckdb.connect()

        # Register table with backend
        name = table_name or "temp_table"
        return backend.create_table(name, arrow_table, overwrite=True)

    def to_pyarrow(self, df: Any) -> "pa.Table":
        """Convert to PyArrow Table via Narwhals."""
        nw = _import_narwhals()

        wrapped = self._wrap(df)

        # Use Narwhals to_arrow if available, otherwise go through Polars
        if hasattr(wrapped, "to_arrow"):
            return wrapped.to_arrow()

        # Fallback: convert to Polars first, then to Arrow
        polars_df = wrapped.to_polars()
        return polars_df.to_arrow()

    # =========================================================================
    # Introspect Operations
    # =========================================================================

    def get_shape(self, df: Any) -> Tuple[int, int]:
        """Get (rows, columns) shape."""
        wrapped = self._wrap(df)
        return wrapped.shape

    def get_column_names(self, df: Any) -> List[str]:
        """Get list of column names."""
        wrapped = self._wrap(df)
        return wrapped.columns

    def get_columns(self, df: Any) -> List[str]:
        """Alias for get_column_names."""
        return self.get_column_names(df)

    def get_schema(self, df: Any) -> Dict[str, Any]:
        """Get column names and their types."""
        wrapped = self._wrap(df)
        schema = wrapped.schema
        return {name: str(dtype) for name, dtype in schema.items()}

    def get_dtypes(self, df: Any) -> Dict[str, Any]:
        """Get column data types."""
        wrapped = self._wrap(df)
        return dict(wrapped.schema)

    # =========================================================================
    # Select Operations
    # =========================================================================

    def select(self, df: Any, columns: List[str]) -> Any:
        """Select columns from DataFrame."""
        nw = _import_narwhals()

        wrapped = self._wrap(df)
        result = wrapped.select([nw.col(c) for c in columns])
        return self._unwrap(result)

    def rename(self, df: Any, mapping: Dict[str, str]) -> Any:
        """Rename columns in DataFrame."""
        wrapped = self._wrap(df)
        result = wrapped.rename(mapping)
        return self._unwrap(result)

    def reorder(self, df: Any, columns: List[str]) -> Any:
        """Reorder columns in DataFrame."""
        return self.select(df, columns)

    def drop(self, df: Any, columns: List[str]) -> Any:
        """Drop columns from DataFrame."""
        wrapped = self._wrap(df)
        result = wrapped.drop(columns)
        return self._unwrap(result)

    # =========================================================================
    # Join Operations
    # =========================================================================

    def join(
        self,
        left: Any,
        right: Any,
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        how: str = "inner",
        suffix: str = "_right",
    ) -> Any:
        """Join two DataFrames via Narwhals."""
        left_wrapped = self._wrap(left)
        right_wrapped = self._wrap(right)

        if on is not None:
            result = left_wrapped.join(right_wrapped, on=on, how=how, suffix=suffix)
        else:
            result = left_wrapped.join(
                right_wrapped,
                left_on=left_on,
                right_on=right_on,
                how=how,
                suffix=suffix,
            )

        return self._unwrap(result)

    # =========================================================================
    # Filter Operations
    # =========================================================================

    def filter(self, df: Any, expression: Any) -> Any:
        """
        Filter DataFrame by expression or series.

        Preserves the input type:
        - If df is already Narwhals, returns Narwhals
        - If df is native (pandas/PyArrow), wraps, filters, and unwraps

        Handles both expressions and series:
        - nw.Expr: Used directly
        - Native series (pd.Series, pa.Array): Wrapped in Narwhals if needed

        Special cases:
        - PyArrow Table + PyArrow Array: Uses pyarrow.compute directly
        """
        nw = _import_narwhals()

        # Check if already a Narwhals DataFrame
        is_narwhals_df = hasattr(df, "_compliant_frame")

        # Check expression type
        expr_module = type(expression).__module__
        df_module = type(df).__module__

        # Special case: PyArrow Table + PyArrow Array → use pyarrow.compute
        if df_module.startswith("pyarrow") and expr_module.startswith("pyarrow"):
            import pyarrow.compute as pc
            return pc.filter(df, expression)

        if is_narwhals_df:
            # Already Narwhals DataFrame
            # For native series, we need to wrap it
            if expr_module.startswith("pandas") or expr_module.startswith("polars"):
                wrapped_expr = nw.from_native(expression, series_only=True)
                return df.filter(wrapped_expr)
            elif expr_module.startswith("pyarrow"):
                # Convert PyArrow array via Polars for Narwhals
                pl = _import_polars()
                pl_series = pl.from_arrow(expression)
                wrapped_expr = nw.from_native(pl_series, series_only=True)
                return df.filter(wrapped_expr)
            # For expressions or already-wrapped series, use directly
            return df.filter(expression)
        else:
            # Native DataFrame - wrap, filter, unwrap
            wrapped_df = nw.from_native(df, eager_only=True)

            # Wrap series if needed
            if expr_module.startswith("pandas") or expr_module.startswith("polars"):
                wrapped_expr = nw.from_native(expression, series_only=True)
            elif expr_module.startswith("pyarrow"):
                # Convert PyArrow array to match the wrapped DataFrame's backend
                # Narwhals wrapping pandas/polars can use corresponding series
                pl = _import_polars()
                pl_series = pl.from_arrow(expression)
                wrapped_expr = nw.from_native(pl_series, series_only=True)
            else:
                wrapped_expr = expression

            result = wrapped_df.filter(wrapped_expr)
            return nw.to_native(result)

    # =========================================================================
    # Row Operations
    # =========================================================================

    def head(self, df: Any, n: int = 5) -> Any:
        """Get first n rows."""
        wrapped = self._wrap(df)
        result = wrapped.head(n)
        return self._unwrap(result)

    def tail(self, df: Any, n: int = 5) -> Any:
        """Get last n rows."""
        wrapped = self._wrap(df)
        result = wrapped.tail(n)
        return self._unwrap(result)

    def sample(self, df: Any, n: int = 5) -> Any:
        """Get random sample of n rows."""
        wrapped = self._wrap(df)

        # Narwhals may not have sample - fall back to head if needed
        if hasattr(wrapped, "sample"):
            result = wrapped.sample(n)
        else:
            # Fall back: convert to Polars, sample, convert back
            polars_df = wrapped.to_polars()
            sampled = polars_df.sample(n)
            nw = _import_narwhals()
            result = nw.from_native(sampled, eager_only=True)

        return self._unwrap(result)

    # =========================================================================
    # Lazy/Eager Operations (Narwhals is primarily eager)
    # =========================================================================

    def is_lazy(self, df: Any) -> bool:
        """Check if DataFrame is lazy (Narwhals is primarily eager)."""
        return False

    def collect(self, df: Any) -> Any:
        """Collect lazy DataFrame to eager (no-op for Narwhals)."""
        return df

    def lazy(self, df: Any) -> Any:
        """Convert eager DataFrame to lazy (not supported - returns as-is)."""
        return df
