"""
CastNamespace - DataFrame type conversion operations.

Provides terminal operations that convert the DataFrame to a specific type.
These are NOT chainable - they return the converted DataFrame directly.

Provides:
    - to_polars() - Convert to Polars DataFrame
    - to_pandas() - Convert to pandas DataFrame
    - to_pyarrow() - Convert to PyArrow Table
    - to_narwhals() - Convert to Narwhals DataFrame
    - to_ibis() - Convert to Ibis Table
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import pandas as pd
    import pyarrow as pa
    import ibis.expr.types as ir

from ..base import BaseNamespace
from ...protocols import CastBuilderProtocol


class CastNamespace(BaseNamespace, CastBuilderProtocol):
    """
    Namespace for DataFrame type conversion (terminal operations).

    These methods are terminal - they return the converted DataFrame,
    not a TableBuilder, ending the method chain.
    """

    def to_polars(self, *, as_lazy: bool = False) -> Any:
        """
        Convert to Polars DataFrame or LazyFrame.

        Args:
            as_lazy: If True, return LazyFrame instead of DataFrame

        Returns:
            Polars DataFrame or LazyFrame

        Example:
            polars_df = table(pandas_df).select("id", "name").to_polars()
        """
        return self._system.to_polars(self._df, as_lazy=as_lazy)

    def to_pandas(self) -> "pd.DataFrame":
        """
        Convert to pandas DataFrame.

        Returns:
            pandas DataFrame

        Example:
            pandas_df = table(polars_df).filter(...).to_pandas()
        """
        return self._system.to_pandas(self._df)

    def to_pyarrow(self) -> "pa.Table":
        """
        Convert to PyArrow Table.

        Returns:
            PyArrow Table

        Example:
            arrow_table = table(df).select("id", "name").to_pyarrow()
        """
        return self._system.to_pyarrow(self._df)

    def to_narwhals(self, *, eager_only: bool = True) -> Any:
        """
        Convert to Narwhals DataFrame.

        Args:
            eager_only: If True, only support eager DataFrames

        Returns:
            Narwhals DataFrame

        Example:
            nw_df = table(df).to_narwhals()
        """
        return self._system.to_narwhals(self._df, eager_only=eager_only)

    def to_ibis(
        self,
        *,
        backend: Optional[Any] = None,
        table_name: Optional[str] = None,
    ) -> "ir.Table":
        """
        Convert to Ibis Table.

        Args:
            backend: Ibis backend connection (default: in-memory DuckDB)
            table_name: Name for the table in the backend

        Returns:
            Ibis Table

        Example:
            ibis_table = table(df).to_ibis(backend=conn, table_name="my_table")
        """
        return self._system.to_ibis(self._df, backend=backend, table_name=table_name)

    def to_native(self) -> Any:
        """
        Return the underlying native DataFrame.

        This is the same as accessing .df property.

        Returns:
            Native DataFrame in its original type

        Example:
            native_df = table(df).select("id").to_native()
        """
        return self._df

    def to_dict(self, *, as_series: bool = False) -> dict:
        """
        Convert to Python dictionary.

        Args:
            as_series: If True, values are Series; if False, values are lists

        Returns:
            Dict mapping column names to values

        Example:
            data = table(df).to_dict()
        """
        # Convert to Polars first for consistent behavior
        polars_df = self._system.to_polars(self._df, as_lazy=False)

        if as_series:
            return polars_df.to_dict(as_series=True)
        else:
            return polars_df.to_dict(as_series=False)

    def to_dicts(self) -> list:
        """
        Convert to list of dictionaries (row-oriented).

        Returns:
            List of dicts, one per row

        Example:
            rows = table(df).to_dicts()
        """
        polars_df = self._system.to_polars(self._df, as_lazy=False)
        return polars_df.to_dicts()

    def to_list(self, column: str) -> list:
        """
        Get a single column as a Python list.

        Args:
            column: Column name

        Returns:
            List of values

        Example:
            ids = table(df).to_list("id")
        """
        polars_df = self._system.to_polars(self._df, as_lazy=False)
        return polars_df[column].to_list()
