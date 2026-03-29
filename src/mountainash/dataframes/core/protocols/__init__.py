"""
Protocol definitions for DataFrame operations.

Following the mountainash-expressions pattern, protocols define the interface
at two levels:

1. System Protocols (Layer 1) - Backend implementations
   - CastProtocol: DataFrame type conversions (to_polars, to_pandas, etc.)
   - IntrospectProtocol: DataFrame introspection (shape, columns, schema)
   - SelectProtocol: Column selection and manipulation
   - JoinProtocol: DataFrame join operations
   - FilterProtocol: Row filtering with expressions
   - RowProtocol: Row-based operations (head, tail, sample)
   - LazyProtocol: Lazy/eager operations (for backends that support it)
   - DataFrameSystemProtocol: Combined system interface

2. Builder Protocols (Layer 2) - Fluent API namespaces
   - SelectBuilderProtocol: Column selection namespace
   - FilterBuilderProtocol: Filtering namespace
   - JoinBuilderProtocol: Join operations namespace
   - RowBuilderProtocol: Row operations namespace
   - CastBuilderProtocol: Type conversion namespace (terminal ops)
   - LazyBuilderProtocol: Lazy/eager namespace
   - TableBuilderProtocol: Combined builder interface
"""

from typing import Protocol, runtime_checkable, Any, Optional, Tuple, List, Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl
    import pandas as pd
    import pyarrow as pa
    import ibis.expr.types as ir


# =============================================================================
# Cast Protocol - DataFrame Type Conversions
# =============================================================================


@runtime_checkable
class CastProtocol(Protocol):
    """Protocol for DataFrame type conversions."""

    def to_polars(self, df: Any, *, as_lazy: bool = False) -> Any:
        """Convert DataFrame to Polars DataFrame or LazyFrame."""
        ...

    def to_pandas(self, df: Any) -> "pd.DataFrame":
        """Convert DataFrame to pandas DataFrame."""
        ...

    def to_narwhals(self, df: Any, *, eager_only: bool = True) -> Any:
        """Convert DataFrame to Narwhals DataFrame."""
        ...

    def to_ibis(
        self,
        df: Any,
        *,
        backend: Optional[Any] = None,
        table_name: Optional[str] = None,
    ) -> "ir.Table":
        """Convert DataFrame to Ibis Table."""
        ...

    def to_pyarrow(self, df: Any) -> "pa.Table":
        """Convert DataFrame to PyArrow Table."""
        ...


# =============================================================================
# Introspect Protocol - DataFrame Introspection
# =============================================================================


@runtime_checkable
class IntrospectProtocol(Protocol):
    """Protocol for DataFrame introspection."""

    def get_shape(self, df: Any) -> Tuple[int, int]:
        """Get (rows, columns) shape of DataFrame."""
        ...

    def get_column_names(self, df: Any) -> List[str]:
        """Get list of column names."""
        ...

    def get_columns(self, df: Any) -> List[str]:
        """Alias for get_column_names."""
        ...

    def get_schema(self, df: Any) -> Dict[str, Any]:
        """Get column names and their types."""
        ...

    def get_dtypes(self, df: Any) -> Dict[str, Any]:
        """Get column data types."""
        ...


# =============================================================================
# Select Protocol - Column Selection and Manipulation
# =============================================================================


@runtime_checkable
class SelectProtocol(Protocol):
    """Protocol for DataFrame column selection and manipulation."""

    def select(self, df: Any, columns: List[str]) -> Any:
        """Select columns from DataFrame."""
        ...

    def rename(self, df: Any, mapping: Dict[str, str]) -> Any:
        """Rename columns in DataFrame."""
        ...

    def reorder(self, df: Any, columns: List[str]) -> Any:
        """Reorder columns in DataFrame."""
        ...

    def drop(self, df: Any, columns: List[str]) -> Any:
        """Drop columns from DataFrame."""
        ...


# =============================================================================
# Join Protocol - DataFrame Join Operations
# =============================================================================


@runtime_checkable
class JoinProtocol(Protocol):
    """Protocol for DataFrame join operations."""

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


# =============================================================================
# Filter Protocol - Row Filtering
# =============================================================================


@runtime_checkable
class FilterProtocol(Protocol):
    """Protocol for DataFrame filtering."""

    def filter(self, df: Any, expression: Any) -> Any:
        """Filter DataFrame by expression."""
        ...


# =============================================================================
# Row Protocol - Row-Based Operations
# =============================================================================


@runtime_checkable
class RowProtocol(Protocol):
    """Protocol for row-based operations."""

    def head(self, df: Any, n: int = 5) -> Any:
        """Get first n rows."""
        ...

    def tail(self, df: Any, n: int = 5) -> Any:
        """Get last n rows."""
        ...

    def sample(self, df: Any, n: int = 5) -> Any:
        """Get random sample of n rows."""
        ...


# =============================================================================
# Lazy Protocol - Lazy/Eager Operations
# =============================================================================


@runtime_checkable
class LazyProtocol(Protocol):
    """Protocol for lazy/eager operations (optional for backends that support it)."""

    def is_lazy(self, df: Any) -> bool:
        """Check if DataFrame is lazy."""
        ...

    def collect(self, df: Any) -> Any:
        """Collect lazy DataFrame to eager."""
        ...

    def lazy(self, df: Any) -> Any:
        """Convert eager DataFrame to lazy."""
        ...


# =============================================================================
# Combined Protocol - Full DataFrameSystem Interface
# =============================================================================


@runtime_checkable
class DataFrameSystemProtocol(
    CastProtocol,
    IntrospectProtocol,
    SelectProtocol,
    JoinProtocol,
    FilterProtocol,
    RowProtocol,
    Protocol,
):
    """
    Combined protocol defining the full DataFrameSystem interface.

    This is the complete interface that all DataFrameSystem backends
    must implement. Used for type checking and documentation.
    """

    def is_native_type(self, obj: Any) -> bool:
        """Check if object is a native type for this backend."""
        ...


# Import builder protocols
from .builder_protocols import (
    SelectBuilderProtocol,
    FilterBuilderProtocol,
    JoinBuilderProtocol,
    RowBuilderProtocol,
    CastBuilderProtocol,
    LazyBuilderProtocol,
    TableBuilderProtocol,
)


__all__ = [
    # System Protocols (Layer 1 - backends)
    "CastProtocol",
    "IntrospectProtocol",
    "SelectProtocol",
    "JoinProtocol",
    "FilterProtocol",
    "RowProtocol",
    "LazyProtocol",
    "DataFrameSystemProtocol",
    # Builder Protocols (Layer 2 - namespaces)
    "SelectBuilderProtocol",
    "FilterBuilderProtocol",
    "JoinBuilderProtocol",
    "RowBuilderProtocol",
    "CastBuilderProtocol",
    "LazyBuilderProtocol",
    "TableBuilderProtocol",
]
