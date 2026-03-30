"""Polars aggregate protocol implementations.

Implements aggregation operations for the Polars backend using split protocols.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateArithmeticExpressionSystemProtocol,
    SubstraitAggregateBooleanExpressionSystemProtocol,
    SubstraitAggregateGenericExpressionSystemProtocol,
    SubstraitAggregateStringExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsAggregateStringExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitAggregateStringExpressionSystemProtocol["pl.Expr"]
):
    """Polars implementation of SubstraitAggregateStringExpressionSystemProtocol.

    Implements string aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate String Methods
    # =========================================================================

    def string_agg(
        self,
        input: PolarsExpr,
        /,
        separator: str = ",",
    ) -> PolarsExpr:
        """Concatenate strings with a separator.

        Args:
            x: String expression to concatenate.
            separator: Separator between values.

        Returns:
            Concatenated string expression.
        """
        return input.str.join(separator)
