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
