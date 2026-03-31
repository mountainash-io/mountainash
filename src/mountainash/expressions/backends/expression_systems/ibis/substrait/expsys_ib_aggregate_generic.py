"""Ibis aggregate protocol implementations.

Implements aggregation operations for the Ibis backend using split protocols.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateArithmeticExpressionSystemProtocol,
    SubstraitAggregateBooleanExpressionSystemProtocol,
    SubstraitAggregateGenericExpressionSystemProtocol,
    SubstraitAggregateStringExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr
    from mountainash.expressions.types import IbisExpr


class SubstraitIbisAggregateGenericExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitAggregateGenericExpressionSystemProtocol["IbisValueExpr"]
):
    """Ibis implementation of SubstraitAggregateGenericExpressionSystemProtocol.

    Implements generic aggregation methods.
    """

    def count(
        self,
        x: IbisValueExpr,
        /,
        overflow: Any = None,
    ) -> IbisValueExpr:
        """Count a set of values.

        Counts non-null values.

        Args:
            x: Expression to count.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Count expression.
        """
        return x.count()

    # def count_all(
    #     self,
    #     overflow: Any = None,
    # ) -> IbisValueExpr:
    #     """Count a set of records (not field referenced).

    #     Counts all rows including nulls.

    #     Args:
    #         overflow: Overflow handling (ignored in Ibis).

    #     Returns:
    #         Count expression.
    #     """
    #     return ibis.literal(1).count()

    def any_value(
        self,
        x: IbisValueExpr,
        /,
        ignore_nulls: Any = None,
    ) -> IbisValueExpr:
        """Select an arbitrary value from a group of values.

        Returns the first value in the group.
        If input is empty, returns null.

        Args:
            x: Expression to select from.
            ignore_nulls: Whether to ignore null values.

        Returns:
            First value in group.
        """
        if ignore_nulls:
            return x.first()
        return x.first()
