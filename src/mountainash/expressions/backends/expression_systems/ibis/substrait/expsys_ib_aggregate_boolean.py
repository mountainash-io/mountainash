"""Ibis aggregate protocol implementations.

Implements aggregation operations for the Ibis backend using split protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateBooleanExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisBooleanColumnExpr, IbisValueExpr



class SubstraitIbisAggregateBooleanExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitAggregateBooleanExpressionSystemProtocol["IbisValueExpr"]
):
    """Ibis implementation of SubstraitAggregateBooleanExpressionSystemProtocol.

    Implements boolean aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate Boolean Methods
    # =========================================================================

    def bool_and(self, x: IbisBooleanColumnExpr, /) -> IbisValueExpr:
        """Aggregate AND - true if all values are true.

        Returns false if any value is false.
        Returns null if input is empty or only contains nulls.

        Args:
            x: Boolean expression to aggregate.

        Returns:
            Aggregated boolean expression.
        """
        return x.all()

    def bool_or(self, x: IbisBooleanColumnExpr, /) -> IbisValueExpr:
        """Aggregate OR - true if any value is true.

        Returns true if any value is true.
        Returns null if input is empty or only contains nulls.

        Args:
            x: Boolean expression to aggregate.

        Returns:
            Aggregated boolean expression.
        """
        return x.any()
