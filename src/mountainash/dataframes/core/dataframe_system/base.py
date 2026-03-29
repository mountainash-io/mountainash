"""
DataFrameSystem base class - the core abstraction for DataFrame operations.

This follows the ExpressionSystem pattern from mountainash-expressions:
- Inherits from ALL operation protocols
- Backend implementations compose via multiple inheritance
- Single injection point for all DataFrame operations
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .constants import CONST_DATAFRAME_BACKEND
from ..protocols import (
    CastProtocol,
    IntrospectProtocol,
    SelectProtocol,
    JoinProtocol,
    FilterProtocol,
    RowProtocol,
    LazyProtocol,
)

if TYPE_CHECKING:
    import polars as pl
    import pandas as pd
    import narwhals as nw
    import ibis.expr.types as ir


class DataFrameSystem(
    CastProtocol,
    IntrospectProtocol,
    SelectProtocol,
    JoinProtocol,
    FilterProtocol,
    RowProtocol,
    LazyProtocol,
    ABC,
):
    """
    Abstract base class for backend-specific DataFrame systems.

    Encapsulates all backend-specific operations, providing a uniform
    interface regardless of the underlying DataFrame library.

    Backend implementations should:
    1. Inherit from this class
    2. Implement all abstract methods
    3. Use @register_dataframe_system decorator for auto-registration

    Example:
        @register_dataframe_system(CONST_DATAFRAME_BACKEND.POLARS)
        class PolarsDataFrameSystem(DataFrameSystem):
            @property
            def backend_type(self) -> CONST_DATAFRAME_BACKEND:
                return CONST_DATAFRAME_BACKEND.POLARS

            def to_pandas(self, df: pl.DataFrame) -> pd.DataFrame:
                return df.to_pandas()
            # ... other implementations
    """

    # =========================================================================
    # Backend Identification
    # =========================================================================

    @property
    @abstractmethod
    def backend_type(self) -> CONST_DATAFRAME_BACKEND:
        """Return the backend type this system handles."""
        ...

    @abstractmethod
    def is_native_type(self, obj: Any) -> bool:
        """Check if object is a native type for this backend."""
        ...

    # =========================================================================
    # Cast Operations (CastProtocol)
    # =========================================================================

    @abstractmethod
    def to_polars(self, df: Any, *, as_lazy: bool = False) -> Any:
        """Convert DataFrame to Polars DataFrame or LazyFrame."""
        ...

    @abstractmethod
    def to_pandas(self, df: Any) -> "pd.DataFrame":
        """Convert DataFrame to pandas DataFrame."""
        ...

    @abstractmethod
    def to_narwhals(self, df: Any, *, eager_only: bool = True) -> Any:
        """Convert DataFrame to Narwhals DataFrame."""
        ...

    @abstractmethod
    def to_ibis(
        self,
        df: Any,
        *,
        backend: Optional[Any] = None,
        table_name: Optional[str] = None,
    ) -> "ir.Table":
        """Convert DataFrame to Ibis Table."""
        ...

    @abstractmethod
    def to_pyarrow(self, df: Any) -> Any:
        """Convert DataFrame to PyArrow Table."""
        ...

    # =========================================================================
    # Introspect Operations (IntrospectProtocol)
    # =========================================================================

    @abstractmethod
    def get_shape(self, df: Any) -> Tuple[int, int]:
        """Get (rows, columns) shape of DataFrame."""
        ...

    @abstractmethod
    def get_column_names(self, df: Any) -> List[str]:
        """Get list of column names."""
        ...

    @abstractmethod
    def get_schema(self, df: Any) -> Dict[str, Any]:
        """Get column names and their types."""
        ...

    @abstractmethod
    def get_dtypes(self, df: Any) -> Dict[str, Any]:
        """Get column data types."""
        ...

    @abstractmethod
    def get_columns(self, df: Any) -> List[str]:
        """Alias for get_column_names."""
        ...

    # =========================================================================
    # Select Operations (SelectProtocol)
    # =========================================================================

    @abstractmethod
    def select(self, df: Any, columns: List[str]) -> Any:
        """Select columns from DataFrame."""
        ...

    @abstractmethod
    def rename(self, df: Any, mapping: Dict[str, str]) -> Any:
        """Rename columns in DataFrame."""
        ...

    @abstractmethod
    def reorder(self, df: Any, columns: List[str]) -> Any:
        """Reorder columns in DataFrame."""
        ...

    @abstractmethod
    def drop(self, df: Any, columns: List[str]) -> Any:
        """Drop columns from DataFrame."""
        ...

    # =========================================================================
    # Join Operations (JoinProtocol)
    # =========================================================================

    @abstractmethod
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
        """Join two DataFrames."""
        ...

    # =========================================================================
    # Filter Operations (FilterProtocol)
    # =========================================================================

    @abstractmethod
    def filter(self, df: Any, expression: Any) -> Any:
        """Filter DataFrame by expression."""
        ...

    # =========================================================================
    # Row Operations
    # =========================================================================

    @abstractmethod
    def head(self, df: Any, n: int = 5) -> Any:
        """Get first n rows."""
        ...

    @abstractmethod
    def tail(self, df: Any, n: int = 5) -> Any:
        """Get last n rows."""
        ...

    @abstractmethod
    def sample(self, df: Any, n: int = 5) -> Any:
        """Get random sample of n rows."""
        ...

    # =========================================================================
    # Lazy/Eager Operations (for backends that support it)
    # =========================================================================

    def is_lazy(self, df: Any) -> bool:
        """Check if DataFrame is lazy (default: False)."""
        return False

    def collect(self, df: Any) -> Any:
        """Collect lazy DataFrame to eager (default: return as-is)."""
        return df

    def lazy(self, df: Any) -> Any:
        """Convert eager DataFrame to lazy (default: return as-is)."""
        return df
