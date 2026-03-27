"""
Builder Protocols for TableBuilder namespaces.

Following the mountainash-expressions pattern, Builder Protocols define the
fluent API contract that namespaces must implement. These ensure consistent
method signatures across all namespaces.

Protocol Hierarchy:
- SelectBuilderProtocol: Column selection and manipulation
- FilterBuilderProtocol: Row filtering operations
- JoinBuilderProtocol: DataFrame join operations
- RowBuilderProtocol: Row-based operations (head, tail, sample)
- CastBuilderProtocol: DataFrame type conversions (terminal operations)
- LazyBuilderProtocol: Lazy/eager execution control
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Protocol, Union, runtime_checkable

if TYPE_CHECKING:
    from ..table_builder.base import BaseTableBuilder


# =============================================================================
# Select Builder Protocol
# =============================================================================


@runtime_checkable
class SelectBuilderProtocol(Protocol):
    """
    Protocol for column selection and manipulation operations.

    Implemented by: SelectNamespace
    """

    def select(self, *columns: str) -> "BaseTableBuilder":
        """Select columns from DataFrame."""
        ...

    def drop(self, *columns: str) -> "BaseTableBuilder":
        """Drop columns from DataFrame."""
        ...

    def rename(self, mapping: Dict[str, str]) -> "BaseTableBuilder":
        """Rename columns in DataFrame."""
        ...

    def reorder(self, *columns: str) -> "BaseTableBuilder":
        """Reorder columns in DataFrame."""
        ...

    def alias(self, column: str, new_name: str) -> "BaseTableBuilder":
        """Alias (rename) a single column."""
        ...

    def keep(self, *columns: str) -> "BaseTableBuilder":
        """Keep only specified columns (alias for select)."""
        ...

    def exclude(self, *columns: str) -> "BaseTableBuilder":
        """Exclude specified columns (alias for drop)."""
        ...


# =============================================================================
# Filter Builder Protocol
# =============================================================================


@runtime_checkable
class FilterBuilderProtocol(Protocol):
    """
    Protocol for row filtering operations.

    Implemented by: FilterNamespace
    """

    def filter(
        self,
        expression: Union[Any, Callable[["BaseTableBuilder"], Any]],
    ) -> "BaseTableBuilder":
        """Filter DataFrame rows by expression."""
        ...

    def where(
        self,
        expression: Union[Any, Callable[["BaseTableBuilder"], Any]],
    ) -> "BaseTableBuilder":
        """Alias for filter."""
        ...

    def query(
        self,
        expression: Union[Any, Callable[["BaseTableBuilder"], Any]],
    ) -> "BaseTableBuilder":
        """Alias for filter (pandas-style naming)."""
        ...

    def filter_by(self, column: str, value: Any) -> "BaseTableBuilder":
        """Filter rows where column equals value."""
        ...

    def filter_not_null(self, column: str) -> "BaseTableBuilder":
        """Filter rows where column is not null."""
        ...

    def filter_null(self, column: str) -> "BaseTableBuilder":
        """Filter rows where column is null."""
        ...


# =============================================================================
# Join Builder Protocol
# =============================================================================


@runtime_checkable
class JoinBuilderProtocol(Protocol):
    """
    Protocol for DataFrame join operations.

    Implemented by: JoinNamespace
    """

    def join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        how: str = "inner",
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """Join with another DataFrame."""
        ...

    def inner_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """Inner join with another DataFrame."""
        ...

    def left_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """Left join with another DataFrame."""
        ...

    def right_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """Right join with another DataFrame."""
        ...

    def outer_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """Outer (full) join with another DataFrame."""
        ...

    def full_join(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """Alias for outer_join."""
        ...

    def merge(
        self,
        right: Union["BaseTableBuilder", Any],
        *,
        on: Optional[str] = None,
        left_on: Optional[str] = None,
        right_on: Optional[str] = None,
        how: str = "inner",
        suffix: str = "_right",
    ) -> "BaseTableBuilder":
        """Alias for join (pandas-style naming)."""
        ...


# =============================================================================
# Row Builder Protocol
# =============================================================================


@runtime_checkable
class RowBuilderProtocol(Protocol):
    """
    Protocol for row-based operations.

    Implemented by: RowNamespace
    """

    def head(self, n: int = 5) -> "BaseTableBuilder":
        """Get first n rows."""
        ...

    def tail(self, n: int = 5) -> "BaseTableBuilder":
        """Get last n rows."""
        ...

    def sample(self, n: int = 5) -> "BaseTableBuilder":
        """Get random sample of n rows."""
        ...

    def limit(self, n: int) -> "BaseTableBuilder":
        """Limit to first n rows (alias for head)."""
        ...

    def take(self, n: int) -> "BaseTableBuilder":
        """Take first n rows (alias for head)."""
        ...

    def first(self) -> "BaseTableBuilder":
        """Get first row."""
        ...

    def last(self) -> "BaseTableBuilder":
        """Get last row."""
        ...

    def slice(self, offset: int, length: Optional[int] = None) -> "BaseTableBuilder":
        """Get a slice of rows."""
        ...

    def skip(self, n: int) -> "BaseTableBuilder":
        """Skip first n rows."""
        ...

    def offset(self, n: int) -> "BaseTableBuilder":
        """Alias for skip (SQL-style naming)."""
        ...


# =============================================================================
# Cast Builder Protocol (Terminal Operations)
# =============================================================================


@runtime_checkable
class CastBuilderProtocol(Protocol):
    """
    Protocol for DataFrame type conversion (terminal operations).

    These methods end the builder chain by returning native DataFrames.

    Implemented by: CastNamespace
    """

    def to_polars(self, *, as_lazy: bool = False) -> Any:
        """Convert to Polars DataFrame or LazyFrame."""
        ...

    def to_pandas(self) -> Any:
        """Convert to pandas DataFrame."""
        ...

    def to_pyarrow(self) -> Any:
        """Convert to PyArrow Table."""
        ...

    def to_narwhals(self, *, eager_only: bool = True) -> Any:
        """Convert to Narwhals DataFrame."""
        ...

    def to_ibis(
        self,
        *,
        backend: Optional[Any] = None,
        table_name: Optional[str] = None,
    ) -> Any:
        """Convert to Ibis Table."""
        ...

    def to_native(self) -> Any:
        """Return the underlying native DataFrame."""
        ...

    def to_dict(self, *, as_series: bool = False) -> dict:
        """Convert to Python dictionary."""
        ...

    def to_dicts(self) -> list:
        """Convert to list of dictionaries (row-oriented)."""
        ...

    def to_list(self, column: str) -> list:
        """Get a single column as a Python list."""
        ...


# =============================================================================
# Lazy Builder Protocol
# =============================================================================


@runtime_checkable
class LazyBuilderProtocol(Protocol):
    """
    Protocol for lazy/eager execution operations.

    Implemented by: LazyNamespace
    """

    def collect(self) -> "BaseTableBuilder":
        """Collect lazy DataFrame to eager."""
        ...

    def lazy(self) -> "BaseTableBuilder":
        """Convert eager DataFrame to lazy."""
        ...

    def execute(self) -> "BaseTableBuilder":
        """Execute and collect results (alias for collect)."""
        ...

    def materialize(self) -> "BaseTableBuilder":
        """Materialize lazy computation (alias for collect)."""
        ...

    def cache(self) -> "BaseTableBuilder":
        """Cache the current state."""
        ...

    def persist(self) -> "BaseTableBuilder":
        """Alias for cache."""
        ...


# =============================================================================
# Combined Builder Protocol
# =============================================================================


@runtime_checkable
class TableBuilderProtocol(
    SelectBuilderProtocol,
    FilterBuilderProtocol,
    JoinBuilderProtocol,
    RowBuilderProtocol,
    CastBuilderProtocol,
    LazyBuilderProtocol,
    Protocol,
):
    """
    Combined protocol defining the full TableBuilder fluent API.

    This is the complete interface that TableBuilder must implement.
    All methods are available via flat namespace dispatch.
    """

    pass


__all__ = [
    # Individual builder protocols
    "SelectBuilderProtocol",
    "FilterBuilderProtocol",
    "JoinBuilderProtocol",
    "RowBuilderProtocol",
    "CastBuilderProtocol",
    "LazyBuilderProtocol",
    # Combined protocol
    "TableBuilderProtocol",
]
