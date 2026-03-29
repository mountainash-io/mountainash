"""
Table Builder - Fluent API for DataFrame Operations.

This module provides the TableBuilder class and entry point functions
for a chainable, fluent interface to DataFrame operations.

Architecture:
    - TableBuilder: Main class wrapping DataFrames with chainable methods
    - Namespaces: Grouped operations (select, filter, join, row, cast, lazy)
    - Entry Points: Factory functions (table, from_polars, from_pandas, etc.)

Example:
    from mountainash_dataframes import table

    # Basic usage
    result = (
        table(df)
        .select("id", "name", "value")
        .filter(lambda t: t["value"] > 100)
        .rename({"value": "amount"})
        .head(10)
        .to_pandas()
    )

    # Join with another DataFrame
    joined = (
        table(users)
        .left_join(orders, on="user_id")
        .select("user_id", "name", "order_total")
        .to_polars()
    )

    # From dict
    builder = from_dict({"a": [1, 2, 3], "b": [4, 5, 6]})
"""

from .base import BaseTableBuilder, BaseNamespace, NamespaceDescriptor
from .table_builder import (
    TableBuilder,
    table,
    from_polars,
    from_pandas,
    from_pyarrow,
    from_ibis,
    from_dict,
    from_records,
)

__all__ = [
    # Main class
    "TableBuilder",
    # Entry points
    "table",
    "from_polars",
    "from_pandas",
    "from_pyarrow",
    "from_ibis",
    "from_dict",
    "from_records",
    # Base classes (for extension)
    "BaseTableBuilder",
    "BaseNamespace",
    "NamespaceDescriptor",
]
