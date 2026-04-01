"""Narwhals aggregate protocol implementations.

Implements aggregation operations for the Narwhals backend using split protocols.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING


from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateGenericExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsAggregateGenericExpressionSystem(
    NarwhalsBaseExpressionSystem,
    SubstraitAggregateGenericExpressionSystemProtocol["nw.Expr"]
):
    """Narwhals implementation of SubstraitAggregateGenericExpressionSystemProtocol.

    Implements generic aggregation methods.
    """

    def count(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Count a set of values.

        Counts non-null values.

        Args:
            x: Expression to count.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Count expression.
        """
        return x.count()

    # def count_all(
    #     self,
    #     overflow: Any = None,
    # ) -> NarwhalsExpr:
    #     """Count a set of records (not field referenced).

    #     Counts all rows including nulls.

    #     Args:
    #         overflow: Overflow handling (ignored in Narwhals).

    #     Returns:
    #         Count expression.
    #     """
    #     return nw.len()

    def any_value(
        self,
        x: NarwhalsExpr,
        /,
        ignore_nulls: Any = None,
    ) -> NarwhalsExpr:
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
            return x.drop_nulls().first()
        return x.first()
