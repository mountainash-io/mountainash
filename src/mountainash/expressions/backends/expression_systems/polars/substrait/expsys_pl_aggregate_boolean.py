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


class SubstraitPolarsAggregateBooleanExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitAggregateBooleanExpressionSystemProtocol["pl.Expr"]
):
    """Polars implementation of SubstraitAggregateBooleanExpressionSystemProtocol.

    Implements boolean aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate Boolean Methods
    # =========================================================================

    def bool_and(self, x: PolarsExpr, /) -> PolarsExpr:
        """Aggregate AND - true if all values are true.

        Returns false if any value is false.
        Returns null if input is empty or only contains nulls.

        Args:
            x: Boolean expression to aggregate.

        Returns:
            Aggregated boolean expression.
        """
        return x.all()

    def bool_or(self, x: PolarsExpr, /) -> PolarsExpr:
        """Aggregate OR - true if any value is true.

        Returns true if any value is true.
        Returns null if input is empty or only contains nulls.

        Args:
            x: Boolean expression to aggregate.

        Returns:
            Aggregated boolean expression.
        """
        return x.any()
