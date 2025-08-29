# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
Ibis Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""

from typing import Callable, Any, Optional, List, Literal
import ibis
import ibis.expr.types as ir
from functools import reduce
import pyarrow as pa
import pyarrow.compute as pc

from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS
from .base_backend_visitor import BaseBackendVisitor

class PyArrowBackendVisitor(BaseBackendVisitor):
    """Ternary-aware Ibis visitor with lambda-based operations following boolean pattern."""

    _backend = "pyarrow"

    def _is_unknown_value(self, array: pa.Array) -> pa.Array:
        """Type-safe UNKNOWN value detection for PyArrow arrays.

        Args:
            array: PyArrow Array to check for UNKNOWN values

        Returns:
            Boolean PyArrow Array indicating if values are UNKNOWN (no nulls in result)
        """
        # Start with null check (covers None, NaN, etc.)
        unknown_mask = pc.is_null(array)
        return pc.fill_null(unknown_mask, False)

        # # Add string UNKNOWN values if applicable
        # try:
        #     if pa.types.is_string(array.type) or pa.types.is_large_string(array.type):

        #         # Use fill_null to handle nulls in comparison result
        #         string_unknown_mask = pc.fill_null(pc.equal(array, "<NA>"), False)
        #         unknown_mask = pc.or_(unknown_mask, string_unknown_mask)
        #     else:
        #         print(f"Skipping string UNKNOWN check for type: {array.type}")
        # except (pa.ArrowInvalid, pa.ArrowTypeError):
        #     # Type mismatch - skip string comparison
        #     raise ValueError("_is_unknown_value failed")

        # # Add numeric UNKNOWN values if applicable
        # try:
        #     if pa.types.is_integer(array.type) or pa.types.is_floating(array.type):
        #         # Use fill_null to handle nulls in comparison result
        #         numeric_unknown_mask = pc.fill_null(pc.equal(array, -999999999), False)
        #         unknown_mask = pc.or_(unknown_mask, numeric_unknown_mask)
        #     else:
        #         print(f"Skipping numeric UNKNOWN check for type: {array.type}")
        # except (pa.ArrowInvalid, pa.ArrowTypeError):
        #     # Type mismatch - skip numeric comparison
        #     raise ValueError("_is_unknown_value failed")

        # # Ensure no nulls in the final mask
        # return pc.fill_null(unknown_mask, False)

    # ===============
    # Comparison Data Prep - ibis concrete implementations
    # ===============


    def _format_column(self,  column: str, table: Any) -> Any:
        return table[column]

    def _format_literal(self, value: Any, table: Any) -> Any:
        if table is None:
            raise ValueError("Table must be provided to format literal in Pyarrow visitor")

        return pa.array([value] * len(table))

    def _format_list(self, value: Any) -> Any:
        return pa.array(list(value)) if not isinstance(value, list) else pa.array(value) # Ensure it's a list
