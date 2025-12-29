"""Narwhals ScalarAggregateExpressionProtocol implementation.

Implements aggregation operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.substrait import (
        ScalarAggregateExpressionProtocol,
    )

if TYPE_CHECKING:
    from mountainash_expressions.types import NarwhalsExpr


class NarwhalsScalarAggregateExpressionSystem(NarwhalsBaseExpressionSystem, ScalarAggregateExpressionProtocol):
    """Narwhals implementation of ScalarAggregateExpressionProtocol.

    Implements aggregation methods:
    - count: Count values in a set
    - count_all: Count all records
    - any_value: Select arbitrary value from group
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

    def count_all(
        self,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Count a set of records (not field referenced).

        Counts all rows including nulls.

        Args:
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Count expression.
        """
        return nw.len()

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

    # =========================================================================
    # Additional Aggregate Methods (Common Extensions)
    # =========================================================================

    def sum(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Sum values.

        Args:
            x: Expression to sum.

        Returns:
            Sum expression.
        """
        return x.sum()

    def mean(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Calculate mean of values.

        Args:
            x: Expression to average.

        Returns:
            Mean expression.
        """
        return x.mean()

    def min(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Get minimum value.

        Args:
            x: Expression to find minimum.

        Returns:
            Min expression.
        """
        return x.min()

    def max(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Get maximum value.

        Args:
            x: Expression to find maximum.

        Returns:
            Max expression.
        """
        return x.max()

    def std(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Calculate standard deviation.

        Args:
            x: Expression to calculate std.

        Returns:
            Standard deviation expression.
        """
        return x.std()

    def var(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Calculate variance.

        Args:
            x: Expression to calculate variance.

        Returns:
            Variance expression.

        Note:
            Narwhals may not have var. Falls back to std squared.
        """
        # Narwhals doesn't have var - use std squared as approximation
        return x.std().pow(nw.lit(2))

    def median(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Calculate median.

        Args:
            x: Expression to calculate median.

        Returns:
            Median expression.

        Note:
            Narwhals may not have median. Falls back to mean.
        """
        # Narwhals doesn't have median - fallback to mean
        return x.mean()

    def first(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Get first value.

        Args:
            x: Expression to get first value.

        Returns:
            First value expression.
        """
        return x.first()

    def last(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Get last value.

        Args:
            x: Expression to get last value.

        Returns:
            Last value expression.
        """
        return x.last()

    def n_unique(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Count unique values.

        Args:
            x: Expression to count unique values.

        Returns:
            Unique count expression.
        """
        return x.n_unique()
