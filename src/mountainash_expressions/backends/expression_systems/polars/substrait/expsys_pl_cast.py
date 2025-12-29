"""Polars CastExpressionProtocol implementation.

Implements type casting operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr



# Mapping from string type names to Polars dtypes
_POLARS_DTYPE_MAP = {
    # Substrait standard names
    "i8": pl.Int8,
    "i16": pl.Int16,
    "i32": pl.Int32,
    "i64": pl.Int64,
    "fp32": pl.Float32,
    "fp64": pl.Float64,
    "f32": pl.Float32,
    "f64": pl.Float64,
    "string": pl.Utf8,
    "bool": pl.Boolean,
    "boolean": pl.Boolean,
    "date": pl.Date,
    "timestamp": pl.Datetime,
    # Common string representations from str(pl.Type)
    "Int8": pl.Int8,
    "Int16": pl.Int16,
    "Int32": pl.Int32,
    "Int64": pl.Int64,
    "Float32": pl.Float32,
    "Float64": pl.Float64,
    "Utf8": pl.Utf8,
    "String": pl.Utf8,
    "Boolean": pl.Boolean,
    "Date": pl.Date,
    "Datetime": pl.Datetime,
    # Python type names
    "int": pl.Int64,
    "float": pl.Float64,
    "str": pl.Utf8,
    # Common aliases
    "int64": pl.Int64,
    "int32": pl.Int32,
    "float64": pl.Float64,
    "float32": pl.Float32,
}


class PolarsCastExpressionSystem(PolarsBaseExpressionSystem, SubstraitCastExpressionSystemProtocol):
    """Polars implementation of CastExpressionProtocol."""

    def cast(self, x: PolarsExpr, /, dtype: Any) -> PolarsExpr:
        """Cast an expression to a target data type.

        Args:
            x: The expression to cast.
            dtype: The target data type (string name or Polars dtype).

        Returns:
            A Polars expression cast to the specified type.
        """
        # If already a Polars dtype, use directly
        if isinstance(dtype, pl.DataType) or (isinstance(dtype, type) and issubclass(dtype, pl.DataType)):
            return x.cast(dtype)

        # Convert string to Polars dtype
        if isinstance(dtype, str):
            polars_dtype = _POLARS_DTYPE_MAP.get(dtype)
            if polars_dtype is not None:
                return x.cast(polars_dtype)

        # Fallback: try to use as-is
        return x.cast(dtype)
