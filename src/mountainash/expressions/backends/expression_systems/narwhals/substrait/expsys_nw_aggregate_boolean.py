"""Narwhals aggregate protocol implementations.

Implements aggregation operations for the Narwhals backend using split protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateBooleanExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr



class SubstraitNarwhalsAggregateBooleanExpressionSystem(
    NarwhalsBaseExpressionSystem,
    SubstraitAggregateBooleanExpressionSystemProtocol["nw.Expr"]
):
    """Narwhals implementation of SubstraitAggregateBooleanExpressionSystemProtocol.

    Implements boolean aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate Boolean Methods
    # =========================================================================

    def bool_and(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Aggregate AND - true if all values are true.

        Returns false if any value is false.
        Returns null if input is empty or only contains nulls.

        Args:
            x: Boolean expression to aggregate.

        Returns:
            Aggregated boolean expression.
        """
        return x.all()

    def bool_or(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Aggregate OR - true if any value is true.

        Returns true if any value is true.
        Returns null if input is empty or only contains nulls.

        Args:
            x: Boolean expression to aggregate.

        Returns:
            Aggregated boolean expression.
        """
        return x.any()
