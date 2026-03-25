"""Polars MountainashNullExpressionProtocol implementation.

Implements null handling extensions for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshNullExpressionSystemProtocol


if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr



class MountainAshPolarsNullExpressionSystem(PolarsBaseExpressionSystem, MountainAshNullExpressionSystemProtocol):
    """Polars implementation of MountainashNullExpressionProtocol.

    Implements null handling extension methods:
    - fill_null: Replace NULL values with a specified value
    - null_if: Replace values equal to a specified value with NULL
    """

    def fill_null(
        self,
        input: PolarsExpr,
        replacement: Any,
        /,
    ) -> PolarsExpr:
        """Replace NULL values with the specified replacement value.

        Args:
            input: Expression that may contain NULL values.
            replacement: Value to use in place of NULLs.

        Returns:
            Expression with NULLs replaced by the replacement value.
        """
        return input.fill_null(replacement)

    def null_if(
        self,
        input: PolarsExpr,
        condition: Any,
        /,
    ) -> PolarsExpr:
        """Replace values equal to condition with NULL.

        SQL NULLIF(input, condition) semantics.
        """
        return pl.when(input.eq(condition)).then(None).otherwise(input)
