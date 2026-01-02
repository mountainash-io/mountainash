"""Ibis CastExpressionProtocol implementation.

Implements type casting operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis
import ibis.expr.datatypes as dt

from ..base import IbisBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr

# Mapping from string type names to Ibis dtypes
_IBIS_DTYPE_MAP = {
    # Substrait standard names
    "i8": "int8",
    "i16": "int16",
    "i32": "int32",
    "i64": "int64",
    "fp32": "float32",
    "fp64": "float64",
    "f32": "float32",
    "f64": "float64",
    "string": "string",
    "bool": "boolean",
    "boolean": "boolean",
    "date": "date",
    "timestamp": "timestamp",
    # Common string representations from Polars/Narwhals
    "Int8": "int8",
    "Int16": "int16",
    "Int32": "int32",
    "Int64": "int64",
    "Float32": "float32",
    "Float64": "float64",
    "Utf8": "string",
    "String": "string",
    "Boolean": "boolean",
    "Date": "date",
    "Datetime": "timestamp",
    # Python type names
    "int": "int64",
    "float": "float64",
    "str": "string",
}


class SubstraitIbisCastExpressionSystem(IbisBaseExpressionSystem, SubstraitCastExpressionSystemProtocol):
    """Ibis implementation of CastExpressionProtocol."""

    def cast(self, x: IbisExpr, /, dtype: Any) -> IbisExpr:
        """Cast an expression to a target data type.

        Args:
            x: The expression to cast.
            dtype: The target data type (string name or Ibis dtype).

        Returns:
            An Ibis expression cast to the specified type.
        """
        # If already an Ibis DataType, use directly
        if isinstance(dtype, dt.DataType):
            return x.cast(dtype)

        # Convert string to Ibis dtype name
        if isinstance(dtype, str):
            ibis_dtype = _IBIS_DTYPE_MAP.get(dtype, dtype)
            return x.cast(ibis_dtype)

        # Fallback: try to use as-is
        return x.cast(dtype)
