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

class SubstraitPolarsAggregateArithmeticExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitAggregateArithmeticExpressionSystemProtocol[pl.Expr]
):
    """Polars implementation of SubstraitAggregateArithmeticExpressionSystemProtocol.

    Implements arithmetic aggregation methods.
    """

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

    # =========================================================================
    # Substrait Aggregate Arithmetic Methods
    # =========================================================================

    def avg(
        self,
        x: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Average a set of values.

        Args:
            x: Expression to average.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Average expression.
        """
        return x.mean()

    def sum0(
        self,
        x: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Sum a set of values. Returns zero for empty set.

        Args:
            x: Expression to sum.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Sum expression (0 for empty).
        """
        return x.sum().fill_null(0)

    def product(
        self,
        x: PolarsExpr,
        /,
        overflow: Any = None,
    ) -> PolarsExpr:
        """Product of a set of values. Returns 1 for empty input.

        Args:
            x: Expression to multiply.
            overflow: Overflow handling (ignored in Polars).

        Returns:
            Product expression.
        """
        return x.product()

    def std_dev(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        distribution: Any = None,
    ) -> PolarsExpr:
        """Calculate standard deviation.

        Args:
            x: Expression to calculate std.
            rounding: Rounding mode (ignored).
            distribution: SAMPLE or POPULATION.

        Returns:
            Standard deviation expression.
        """
        ddof = 0 if distribution == "POPULATION" else 1
        return x.std(ddof=ddof)

    def variance(
        self,
        x: PolarsExpr,
        /,
        rounding: Any = None,
        distribution: Any = None,
    ) -> PolarsExpr:
        """Calculate variance.

        Args:
            x: Expression to calculate variance.
            rounding: Rounding mode (ignored).
            distribution: SAMPLE or POPULATION.

        Returns:
            Variance expression.
        """
        ddof = 0 if distribution == "POPULATION" else 1
        return x.var(ddof=ddof)

    def corr(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
        rounding: Any = None,
    ) -> PolarsExpr:
        """Calculate Pearson correlation coefficient.

        Args:
            x: First expression.
            y: Second expression.
            rounding: Rounding mode (ignored).

        Returns:
            Correlation coefficient.

        Note:
            Polars corr requires struct context. May not work in all cases.
        """
        # Polars doesn't have a direct column-to-column corr in expression API
        raise NotImplementedError(
            "corr() requires struct context in Polars. Use DataFrame.corr() instead."
        )

    def mode(self, x: PolarsExpr, /) -> PolarsExpr:
        """Calculate mode (most frequent value).

        Args:
            x: Expression to find mode.

        Returns:
            Mode expression.
        """
        return x.mode().first()

    def quantile(
        self,
        x: PolarsExpr,
        /,
        q: float = 0.5,
        interpolation: str = "nearest",
    ) -> PolarsExpr:
        """Calculate quantile.

        Args:
            x: Expression to calculate quantile.
            q: Quantile value (0-1).
            interpolation: Interpolation method.

        Returns:
            Quantile expression.
        """
        return x.quantile(q, interpolation=interpolation)


class SubstraitPolarsAggregateBooleanExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitAggregateBooleanExpressionSystemProtocol[pl.Expr]
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


class SubstraitPolarsAggregateGenericExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitAggregateGenericExpressionSystemProtocol[pl.Expr]
):
    """Polars implementation of SubstraitAggregateGenericExpressionSystemProtocol.

    Implements generic aggregation methods.
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


class SubstraitPolarsAggregateStringExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitAggregateStringExpressionSystemProtocol[pl.Expr]
):
    """Polars implementation of SubstraitAggregateStringExpressionSystemProtocol.

    Implements string aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate String Methods
    # =========================================================================

    def string_agg(
        self,
        x: PolarsExpr,
        separator: str = ",",
        /,
    ) -> PolarsExpr:
        """Concatenate strings with a separator.

        Args:
            x: String expression to concatenate.
            separator: Separator between values.

        Returns:
            Concatenated string expression.
        """
        return x.str.join(separator)
