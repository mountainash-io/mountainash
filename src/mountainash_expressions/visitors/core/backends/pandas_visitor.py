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
import pandas as pd
from mountainash_dataframes.constants import CONST_EXPRESSION_LOGIC_OPERATORS
from .base_backend_visitor import BaseBackendVisitor

class PandasBackendVisitor(BaseBackendVisitor):
    """Ternary-aware Ibis visitor with lambda-based operations following boolean pattern."""

    _backend = "pandas"

    def _is_unknown_value(self, series: pd.Series) -> pd.Series:
        """Type-safe UNKNOWN value detection for pandas Series.

        Args:
            series: Pandas Series to check for UNKNOWN values

        Returns:
            Boolean pandas Series indicating if values are UNKNOWN
        """
        # Handle pandas-specific null types: NaN, None, pd.NA
        unknown_mask = series.isna()  # Covers NaN, None, pd.NA

        # # Add string UNKNOWN values
        # try:
        #     unknown_mask = unknown_mask | (series == "<NA>")
        # except (TypeError, ValueError):
        #     # Type mismatch - skip string comparison
        #     pass

        # # Add numeric UNKNOWN values
        # try:
        #     unknown_mask = unknown_mask | (series == -999999999)
        # except (TypeError, ValueError):
        #     # Type mismatch - skip numeric comparison
        #     pass

        return unknown_mask

    # ===============
    # Comparison Data Prep - ibis concrete implementations
    # ===============

    def _format_column(self,  column: str, table: Any) -> Any:
        return table[column]

    def _format_literal(self, value: Any, table: pd.DataFrame) -> Any:
        if table is None:
            raise ValueError("Table must be provided to format literal in Pandas visitor")
        return pd.Series([value] * len(table), index=table.index)

    def _format_list(self, value: Any) -> Any:
        return list(value) if not isinstance(value, list) else value
