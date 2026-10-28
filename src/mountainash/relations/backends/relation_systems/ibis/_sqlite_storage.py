"""SQLite storage check: reject Arrow values SQLite would silently change or fail to bind."""

from __future__ import annotations

import math
from typing import Any


def check(arrow: Any) -> None:
    import pyarrow as pa

    for field, column in zip(arrow.schema, arrow.columns):
        if pa.types.is_floating(field.type) and any(
            isinstance(item, float) and math.isnan(item) for item in column.to_pylist()
        ):
            raise ValueError("SQLite stores IEEE NaN as SQL NULL")
        if pa.types.is_decimal(field.type) and column.null_count != len(column):
            raise ValueError("SQLite cannot bind non-null decimal.Decimal values")
        if pa.types.is_nested(field.type):
            raise ValueError(f"SQLite has no storage for nested type {field.type}")


def check_owned(arrow: Any) -> None:
    """Extra limits on an owned (``create_table``) SQLite copy.

    Ibis 12's SQLite ``create_table`` fails on any decimal column, including an
    all-null one that the memtable path stores (backlog 336); refuse it typed.
    """
    import pyarrow as pa

    for field in arrow.schema:
        if pa.types.is_decimal(field.type):
            raise ValueError("SQLite create_table cannot hold a decimal column (Ibis, backlog 336)")
