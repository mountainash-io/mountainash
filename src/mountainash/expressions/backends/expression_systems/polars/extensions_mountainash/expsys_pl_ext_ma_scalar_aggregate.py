"""Polars ScalarAggregateExpressionProtocol implementation.

Implements aggregation operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainashExtensionAggregateExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr

# Type alias for expression type

class SubstraitPolarsScalarAggregateExpressionSystem(
    PolarsBaseExpressionSystem,
    MountainashExtensionAggregateExpressionSystemProtocol[pl.Expr],
):
    """Polars implementation of ScalarAggregateExpressionProtocol.

    Implements aggregation methods:
    - count: Count values in a set
    - count_all: Count all records
    - any_value: Select arbitrary value from group
    """

    def count(
        self,
        x: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Count a set of values.

        Counts non-null values.

        Args:
            x: Expression to count.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Count expression.
        """
        return x.count()

    def count_all(
        self,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Count a set of records (not field referenced).

        Counts all rows including nulls.

        Args:
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Count expression.
        """
        return pl.count()

    def any_value(
        self,
        x: PolarsExpr,
        /,
        ignore_nulls: Any = None,
    ) -> PolarsExpr:
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

    # =========================================================================
    # Additional Aggregate Methods (Common Extensions)
    # =========================================================================

    def sum(self, x: PolarsExpr, /) -> PolarsExpr:
        """Sum values.

        Args:
            x: Expression to sum.

        Returns:
            Sum expression.
        """
        return x.sum()

    def mean(self, x: PolarsExpr, /) -> PolarsExpr:
        """Calculate mean of values.

        Args:
            x: Expression to average.

        Returns:
            Mean expression.
        """
        return x.mean()

    def min(self, x: PolarsExpr, /) -> PolarsExpr:
        """Get minimum value.

        Args:
            x: Expression to find minimum.

        Returns:
            Min expression.
        """
        return x.min()

    def max(self, x: PolarsExpr, /) -> PolarsExpr:
        """Get maximum value.

        Args:
            x: Expression to find maximum.

        Returns:
            Max expression.
        """
        return x.max()

    def std(self, x: PolarsExpr, /) -> PolarsExpr:
        """Calculate standard deviation.

        Args:
            x: Expression to calculate std.

        Returns:
            Standard deviation expression.
        """
        return x.std()

    def var(self, x: PolarsExpr, /) -> PolarsExpr:
        """Calculate variance.

        Args:
            x: Expression to calculate variance.

        Returns:
            Variance expression.
        """
        return x.var()

    def median(self, x: PolarsExpr, /) -> PolarsExpr:
        """Calculate median.

        Args:
            x: Expression to calculate median.

        Returns:
            Median expression.
        """
        return x.median()

    def first(self, x: PolarsExpr, /) -> PolarsExpr:
        """Get first value.

        Args:
            x: Expression to get first value.

        Returns:
            First value expression.
        """
        return x.first()

    def last(self, x: PolarsExpr, /) -> PolarsExpr:
        """Get last value.

        Args:
            x: Expression to get last value.

        Returns:
            Last value expression.
        """
        return x.last()

    def n_unique(self, x: PolarsExpr, /) -> PolarsExpr:
        """Count unique values.

        Args:
            x: Expression to count unique values.

        Returns:
            Unique count expression.
        """
        return x.n_unique()
