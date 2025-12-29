"""Ibis ScalarAggregateExpressionProtocol implementation.

Implements aggregation operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait import (
        ScalarAggregateExpressionProtocol,
    )

# Type alias for expression type
from mountainash_expressions.types import IbisExpr


class IbisScalarAggregateExpressionSystem(IbisBaseExpressionSystem, ScalarAggregateExpressionProtocol):
    """Ibis implementation of ScalarAggregateExpressionProtocol.

    Implements aggregation methods:
    - count: Count values in a set
    - count_all: Count all records
    - any_value: Select arbitrary value from group
    """

    def count(
        self,
        x: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
        """Count a set of values.

        Counts non-null values.

        Args:
            x: Expression to count.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Count expression.
        """
        return x.count()

    def count_all(
        self,
        overflow: Any = None,
    ) -> IbisExpr:
        """Count a set of records (not field referenced).

        Counts all rows including nulls.

        Args:
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Count expression.
        """
        return ibis.literal(1).count()

    def any_value(
        self,
        x: IbisExpr,
        /,
        ignore_nulls: Any = None,
    ) -> IbisExpr:
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

    # =========================================================================
    # Additional Aggregate Methods (Common Extensions)
    # =========================================================================

    def sum(self, x: IbisExpr, /) -> IbisExpr:
        """Sum values.

        Args:
            x: Expression to sum.

        Returns:
            Sum expression.
        """
        return x.sum()

    def mean(self, x: IbisExpr, /) -> IbisExpr:
        """Calculate mean of values.

        Args:
            x: Expression to average.

        Returns:
            Mean expression.
        """
        return x.mean()

    def min(self, x: IbisExpr, /) -> IbisExpr:
        """Get minimum value.

        Args:
            x: Expression to find minimum.

        Returns:
            Min expression.
        """
        return x.min()

    def max(self, x: IbisExpr, /) -> IbisExpr:
        """Get maximum value.

        Args:
            x: Expression to find maximum.

        Returns:
            Max expression.
        """
        return x.max()

    def std(self, x: IbisExpr, /) -> IbisExpr:
        """Calculate standard deviation.

        Args:
            x: Expression to calculate std.

        Returns:
            Standard deviation expression.
        """
        return x.std()

    def var(self, x: IbisExpr, /) -> IbisExpr:
        """Calculate variance.

        Args:
            x: Expression to calculate variance.

        Returns:
            Variance expression.
        """
        return x.var()

    def median(self, x: IbisExpr, /) -> IbisExpr:
        """Calculate median.

        Args:
            x: Expression to calculate median.

        Returns:
            Median expression.
        """
        return x.median()

    def first(self, x: IbisExpr, /) -> IbisExpr:
        """Get first value.

        Args:
            x: Expression to get first value.

        Returns:
            First value expression.
        """
        return x.first()

    def last(self, x: IbisExpr, /) -> IbisExpr:
        """Get last value.

        Args:
            x: Expression to get last value.

        Returns:
            Last value expression.
        """
        return x.last()

    def n_unique(self, x: IbisExpr, /) -> IbisExpr:
        """Count unique values.

        Args:
            x: Expression to count unique values.

        Returns:
            Unique count expression.
        """
        return x.nunique()
