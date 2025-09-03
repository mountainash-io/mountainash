# file: src/mountainash_dataframes/utils/expressions/ternary/ternary_expression_ibis.py

"""
Ibis Ternary Expression Visitor

This module provides a clean, lambda-based approach to ternary logic expressions
that mirrors the boolean system design while handling three-valued logic (TRUE/FALSE/UNKNOWN).
"""

from typing import Any
import pandas as pd
from ...core.constants import CONST_VISITOR_BACKENDS
from ...core.visitor import BackendVisitorMixin

class PandasBackendVisitorMixin(BackendVisitorMixin):
    """Ternary-aware Ibis visitor with lambda-based operations following boolean pattern."""

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        return CONST_VISITOR_BACKENDS.IBIS


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
