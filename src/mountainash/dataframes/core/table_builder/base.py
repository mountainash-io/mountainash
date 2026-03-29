"""
BaseTableBuilder - Fluent API for DataFrame operations.

This module provides the core TableBuilder class that enables fluent/chainable
DataFrame operations, similar to mountainash-expressions.

Architecture:
    - TableBuilder wraps a DataFrame and provides chainable operations
    - Every operation returns a new TableBuilder instance (immutability)
    - Operations are delegated to DataFrameSystem backends
    - Namespaces group related operations (select, filter, join, etc.)

Example:
    from mountainash_dataframes import table

    result = (
        table(df)
        .select("id", "name", "value")
        .filter(lambda t: t["value"] > 100)
        .rename({"value": "amount"})
        .head(10)
        .to_polars()
    )
"""

from __future__ import annotations

from abc import ABC
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

if TYPE_CHECKING:
    import pandas as pd
    import polars as pl
    import pyarrow as pa
    import ibis.expr.types as ir
    from typing_extensions import Self

from ..dataframe_system import DataFrameSystem, DataFrameSystemFactory


class NamespaceDescriptor:
    """
    Descriptor for lazy namespace instantiation.

    Provides explicit namespace accessors like `table.str.upper()` or `table.dt.year()`.
    """

    def __init__(self, namespace_cls: Type["BaseNamespace"]) -> None:
        self._namespace_cls = namespace_cls

    def __get__(self, obj: Optional["BaseTableBuilder"], objtype: Type = None) -> "BaseNamespace":
        if obj is None:
            return self  # type: ignore
        return self._namespace_cls(obj)


class BaseNamespace:
    """
    Base class for all table operation namespaces.

    Namespaces group related operations and hold their implementations.
    Each method in a namespace should return a new TableBuilder instance.
    """

    __slots__ = ("_builder",)

    def __init__(self, builder: "BaseTableBuilder") -> None:
        """Initialize the namespace with parent builder."""
        self._builder = builder

    @property
    def _df(self) -> Any:
        """Access the current DataFrame from parent builder."""
        return self._builder._df

    @property
    def _system(self) -> DataFrameSystem:
        """Access the DataFrameSystem from parent builder."""
        return self._builder._system

    def _build(self, df: Any) -> "BaseTableBuilder":
        """
        Return a new TableBuilder instance with the given DataFrame.

        Uses parent builder's create() to preserve concrete type.
        """
        return self._builder.create(df)


class BaseTableBuilder(ABC):
    """
    Abstract base class for fluent DataFrame API.

    The TableBuilder wraps a DataFrame and provides chainable operations.
    Every operation method returns a new TableBuilder instance, enabling
    fluent method chaining while maintaining immutability.

    Attributes:
        _df: The wrapped DataFrame
        _system: The DataFrameSystem for this DataFrame's backend

    Example:
        builder = TableBuilder(polars_df)
        result = builder.select("a", "b").filter(...).to_pandas()
    """

    __slots__ = ("_df", "_system")

    # Flat namespaces - methods dispatched via __getattr__
    _FLAT_NAMESPACES: ClassVar[Tuple[Type[BaseNamespace], ...]] = ()

    def __init__(self, df: Any) -> None:
        """
        Initialize the builder with a DataFrame.

        Args:
            df: Any supported DataFrame type (Polars, pandas, PyArrow, Ibis)
        """
        self._df = df
        self._system = DataFrameSystemFactory.get_system(df)

    @classmethod
    def create(cls, df: Any) -> "Self":
        """
        Factory method for creating new builder instances.

        Preserves the concrete class type when called from subclasses.
        This is the key method that enables method chaining.

        Args:
            df: DataFrame to wrap

        Returns:
            New TableBuilder instance of the same concrete type
        """
        return cls(df)

    def __getattr__(self, name: str) -> Any:
        """
        Dispatch attribute access to flat namespaces.

        This enables methods from namespaces to be called directly
        on the builder without explicit namespace access.
        """
        for ns_cls in self._FLAT_NAMESPACES:
            if hasattr(ns_cls, name):
                ns = ns_cls(self)
                return getattr(ns, name)
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    # =========================================================================
    # Introspection (non-chainable - return values)
    # =========================================================================

    @property
    def shape(self) -> Tuple[int, int]:
        """Get DataFrame shape as (rows, columns)."""
        return self._system.get_shape(self._df)

    @property
    def columns(self) -> List[str]:
        """Get list of column names."""
        return self._system.get_column_names(self._df)

    @property
    def schema(self) -> Dict[str, Any]:
        """Get column names and their types."""
        return self._system.get_schema(self._df)

    @property
    def dtypes(self) -> Dict[str, Any]:
        """Get column data types."""
        return self._system.get_dtypes(self._df)

    @property
    def is_lazy(self) -> bool:
        """Check if DataFrame is lazy (deferred execution)."""
        return self._system.is_lazy(self._df)

    def __len__(self) -> int:
        """Get row count."""
        return self.shape[0]

    def __repr__(self) -> str:
        """String representation."""
        rows, cols = self.shape
        backend = self._system.backend_type.name
        lazy_str = " (lazy)" if self.is_lazy else ""
        return f"TableBuilder[{backend}]({rows} rows × {cols} cols){lazy_str}"

    # =========================================================================
    # DataFrame Access
    # =========================================================================

    @property
    def df(self) -> Any:
        """
        Access the underlying DataFrame.

        Returns:
            The wrapped DataFrame in its native type
        """
        return self._df

    def __getitem__(self, key: Union[str, List[str]]) -> Any:
        """
        Column access for filter expressions.

        Enables syntax like: table["column"] or table[["col1", "col2"]]

        Args:
            key: Column name or list of column names

        Returns:
            Column expression or selected DataFrame
        """
        if isinstance(key, str):
            # Return column for use in expressions
            # For now, delegate to the native DataFrame's __getitem__
            return self._df[key]
        elif isinstance(key, list):
            # Select multiple columns
            return self.select(*key)
        else:
            raise TypeError(f"Invalid key type: {type(key)}")
