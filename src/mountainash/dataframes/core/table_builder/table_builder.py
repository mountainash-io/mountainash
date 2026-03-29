"""
TableBuilder - The main fluent API class for DataFrame operations.

This module provides the TableBuilder class that combines all operation
namespaces into a single fluent interface.

Example:
    from mountainash_dataframes import table

    result = (
        table(df)
        .select("id", "name", "value")
        .filter(lambda t: t["value"] > 100)
        .rename({"value": "amount"})
        .join(other_df, on="id")
        .head(10)
        .to_polars()
    )
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Tuple, Type

if TYPE_CHECKING:
    from typing_extensions import Self

from .base import BaseTableBuilder, BaseNamespace, NamespaceDescriptor
from .namespaces import (
    SelectNamespace,
    FilterNamespace,
    JoinNamespace,
    RowNamespace,
    CastNamespace,
    LazyNamespace,
)


class TableBuilder(BaseTableBuilder):
    """
    Fluent API for DataFrame operations.

    TableBuilder wraps any supported DataFrame and provides a chainable
    interface for common operations. Every transformation method returns
    a new TableBuilder instance, enabling fluent method chaining.

    Supported backends:
        - Polars (DataFrame and LazyFrame)
        - pandas (via Narwhals)
        - PyArrow (via Narwhals)
        - Ibis (SQL backends)

    Attributes:
        df: The underlying DataFrame
        shape: Tuple of (rows, columns)
        columns: List of column names
        schema: Dict of column names to types
        is_lazy: Whether the DataFrame uses lazy evaluation

    Example:
        from mountainash_dataframes import table

        # Basic chaining
        result = (
            table(df)
            .select("id", "name")
            .filter(lambda t: t["id"] > 100)
            .head(10)
            .to_pandas()
        )

        # Join operations
        joined = (
            table(users)
            .left_join(orders, on="user_id")
            .select("user_id", "name", "order_total")
            .to_polars()
        )

        # Lazy evaluation
        lazy_result = (
            table(df)
            .lazy()
            .filter(...)
            .select(...)
            .collect()
        )
    """

    # Flat namespaces - methods dispatched via __getattr__
    # These enable direct method calls like table.select() instead of table.sel.select()
    _FLAT_NAMESPACES: ClassVar[Tuple[Type[BaseNamespace], ...]] = (
        SelectNamespace,
        FilterNamespace,
        JoinNamespace,
        RowNamespace,
        CastNamespace,
        LazyNamespace,
    )

    # Explicit namespace descriptors for grouped access
    # These enable table.sel.select() style access
    sel = NamespaceDescriptor(SelectNamespace)
    filt = NamespaceDescriptor(FilterNamespace)
    join_ns = NamespaceDescriptor(JoinNamespace)
    row = NamespaceDescriptor(RowNamespace)
    cast = NamespaceDescriptor(CastNamespace)
    exec = NamespaceDescriptor(LazyNamespace)


# =============================================================================
# Entry Point Functions
# =============================================================================


def table(df: Any) -> TableBuilder:
    """
    Create a TableBuilder for fluent DataFrame operations.

    This is the main entry point for the fluent API.

    Args:
        df: Any supported DataFrame (Polars, pandas, PyArrow, Ibis)

    Returns:
        TableBuilder instance for chaining operations

    Example:
        from mountainash_dataframes import table

        result = (
            table(polars_df)
            .select("id", "name", "value")
            .filter(lambda t: t["value"] > 100)
            .to_pandas()
        )
    """
    return TableBuilder(df)


def from_polars(df: Any) -> TableBuilder:
    """
    Create a TableBuilder from a Polars DataFrame or LazyFrame.

    Args:
        df: Polars DataFrame or LazyFrame

    Returns:
        TableBuilder instance

    Example:
        builder = from_polars(pl.DataFrame({"a": [1, 2, 3]}))
    """
    return TableBuilder(df)


def from_pandas(df: Any) -> TableBuilder:
    """
    Create a TableBuilder from a pandas DataFrame.

    Args:
        df: pandas DataFrame

    Returns:
        TableBuilder instance

    Example:
        builder = from_pandas(pd.DataFrame({"a": [1, 2, 3]}))
    """
    return TableBuilder(df)


def from_pyarrow(table_obj: Any) -> TableBuilder:
    """
    Create a TableBuilder from a PyArrow Table.

    Args:
        table_obj: PyArrow Table

    Returns:
        TableBuilder instance

    Example:
        builder = from_pyarrow(pa.table({"a": [1, 2, 3]}))
    """
    return TableBuilder(table_obj)


def from_ibis(table_obj: Any) -> TableBuilder:
    """
    Create a TableBuilder from an Ibis Table.

    Args:
        table_obj: Ibis Table

    Returns:
        TableBuilder instance

    Example:
        conn = ibis.duckdb.connect()
        builder = from_ibis(conn.table("my_table"))
    """
    return TableBuilder(table_obj)


def from_dict(data: dict) -> TableBuilder:
    """
    Create a TableBuilder from a dictionary.

    Converts the dictionary to a Polars DataFrame first.

    Args:
        data: Dict with column names as keys and lists as values

    Returns:
        TableBuilder instance

    Example:
        builder = from_dict({"a": [1, 2, 3], "b": [4, 5, 6]})
    """
    import polars as pl

    df = pl.DataFrame(data)
    return TableBuilder(df)


def from_records(records: list) -> TableBuilder:
    """
    Create a TableBuilder from a list of dictionaries (records).

    Converts to a Polars DataFrame first.

    Args:
        records: List of dicts, one per row

    Returns:
        TableBuilder instance

    Example:
        builder = from_records([
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ])
    """
    import polars as pl

    df = pl.DataFrame(records)
    return TableBuilder(df)
