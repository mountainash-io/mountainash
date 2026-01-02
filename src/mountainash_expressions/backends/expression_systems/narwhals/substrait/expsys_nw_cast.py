"""Narwhals CastExpressionProtocol implementation.

Implements type casting operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitCastExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import NarwhalsExpr


# Mapping from string type names to Narwhals dtypes
_NARWHALS_DTYPE_MAP = {
    # Substrait standard names
    "i8": nw.Int8,
    "i16": nw.Int16,
    "i32": nw.Int32,
    "i64": nw.Int64,
    "fp32": nw.Float32,
    "fp64": nw.Float64,
    "f32": nw.Float32,
    "f64": nw.Float64,
    "string": nw.String,
    "bool": nw.Boolean,
    "boolean": nw.Boolean,
    "date": nw.Date,
    # Common string representations from str(nw.Type)
    "Int8": nw.Int8,
    "Int16": nw.Int16,
    "Int32": nw.Int32,
    "Int64": nw.Int64,
    "Float32": nw.Float32,
    "Float64": nw.Float64,
    "String": nw.String,
    "Utf8": nw.String,
    "Boolean": nw.Boolean,
    "Date": nw.Date,
    "Datetime": nw.Datetime,
    # Python type names
    "int": nw.Int64,
    "float": nw.Float64,
    "str": nw.String,
    # Common aliases
    "int64": nw.Int64,
    "int32": nw.Int32,
    "float64": nw.Float64,
    "float32": nw.Float32,
}


class SubstraitNarwhalsCastExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitCastExpressionSystemProtocol):
    """Narwhals implementation of CastExpressionProtocol."""

    def cast(self, x: NarwhalsExpr, /, dtype: Any) -> NarwhalsExpr:
        """Cast an expression to a target data type.

        Args:
            x: The expression to cast.
            dtype: The target data type (string name or Narwhals dtype).

        Returns:
            A Narwhals expression cast to the specified type.
        """
        # If already a Narwhals dtype, use directly
        if hasattr(nw, "DType") and isinstance(dtype, nw.DType):
            return x.cast(dtype)

        # Check if it's a Narwhals dtype class (like nw.Int64)
        if isinstance(dtype, type) and hasattr(dtype, "__module__") and "narwhals" in str(dtype.__module__):
            return x.cast(dtype)

        # Convert string to Narwhals dtype
        if isinstance(dtype, str):
            narwhals_dtype = _NARWHALS_DTYPE_MAP.get(dtype)
            if narwhals_dtype is not None:
                return x.cast(narwhals_dtype)

        # Fallback: try to use as-is
        return x.cast(dtype)
