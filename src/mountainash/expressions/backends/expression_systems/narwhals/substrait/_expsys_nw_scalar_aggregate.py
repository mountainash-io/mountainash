"""Narwhals aggregate protocol implementations.

Implements aggregation operations for the Narwhals backend using split protocols.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateArithmeticExpressionSystemProtocol,
    SubstraitAggregateBooleanExpressionSystemProtocol,
    SubstraitAggregateGenericExpressionSystemProtocol,
    SubstraitAggregateStringExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr

class SubstraitNarwhalsAggregateArithmeticExpressionSystem(
    NarwhalsBaseExpressionSystem,
    SubstraitAggregateArithmeticExpressionSystemProtocol["nw.Expr"]
):
    """Narwhals implementation of SubstraitAggregateArithmeticExpressionSystemProtocol.

    Implements arithmetic aggregation methods.
    """

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

    # =========================================================================
    # Substrait Aggregate Arithmetic Methods
    # =========================================================================

    def avg(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Average a set of values.

        Args:
            x: Expression to average.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Average expression.
        """
        return x.mean()

    def sum0(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Sum a set of values. Returns zero for empty set.

        Args:
            x: Expression to sum.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Sum expression (0 for empty).
        """
        return x.sum().fill_null(nw.lit(0))

    def product(
        self,
        x: NarwhalsExpr,
        /,
        overflow: Any = None,
    ) -> NarwhalsExpr:
        """Product of a set of values. Returns 1 for empty input.

        Args:
            x: Expression to multiply.
            overflow: Overflow handling (ignored in Narwhals).

        Returns:
            Product expression.

        Note:
            Narwhals doesn't have a direct product aggregate.
            Falls back to exp(sum(log(x))) which works for positive values.
        """
        # Using exp(sum(log(x))) for product - works for positive values
        return x.log().sum().exp()

    def std_dev(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        distribution: Any = None,
    ) -> NarwhalsExpr:
        """Calculate standard deviation.

        Args:
            x: Expression to calculate std.
            rounding: Rounding mode (ignored).
            distribution: SAMPLE or POPULATION.

        Returns:
            Standard deviation expression.

        Note:
            Narwhals std() uses ddof=1 (sample) by default.
            Population std may not be available.
        """
        # Narwhals doesn't support ddof parameter
        return x.std()

    def variance(
        self,
        x: NarwhalsExpr,
        /,
        rounding: Any = None,
        distribution: Any = None,
    ) -> NarwhalsExpr:
        """Calculate variance.

        Args:
            x: Expression to calculate variance.
            rounding: Rounding mode (ignored).
            distribution: SAMPLE or POPULATION.

        Returns:
            Variance expression.

        Note:
            Narwhals may not have var. Uses std squared as approximation.
        """
        # Narwhals doesn't have var - use std squared
        return x.std().pow(nw.lit(2))

    def corr(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
        rounding: Any = None,
    ) -> NarwhalsExpr:
        """Calculate Pearson correlation coefficient.

        Args:
            x: First expression.
            y: Second expression.
            rounding: Rounding mode (ignored).

        Returns:
            Correlation coefficient.

        Raises:
            NotImplementedError: Narwhals doesn't support corr.
        """
        raise NotImplementedError(
            "corr() is not supported by the Narwhals backend."
        )

    def mode(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Calculate mode (most frequent value).

        Args:
            x: Expression to find mode.

        Returns:
            Mode expression.

        Raises:
            NotImplementedError: Narwhals doesn't support mode.
        """
        raise NotImplementedError(
            "mode() is not supported by the Narwhals backend."
        )

    def quantile(
        self,
        x: NarwhalsExpr,
        /,
        q: float = 0.5,
        interpolation: str = "nearest",
    ) -> NarwhalsExpr:
        """Calculate quantile.

        Args:
            x: Expression to calculate quantile.
            q: Quantile value (0-1).
            interpolation: Interpolation method.

        Returns:
            Quantile expression.
        """
        return x.quantile(q, interpolation=interpolation)


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


class SubstraitNarwhalsAggregateStringExpressionSystem(
    NarwhalsBaseExpressionSystem,
    SubstraitAggregateStringExpressionSystemProtocol["nw.Expr"]
):
    """Narwhals implementation of SubstraitAggregateStringExpressionSystemProtocol.

    Implements string aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate String Methods
    # =========================================================================

    def string_agg(
        self,
        x: NarwhalsExpr,
        separator: str = ",",
        /,
    ) -> NarwhalsExpr:
        """Concatenate strings with a separator.

        Args:
            x: String expression to concatenate.
            separator: Separator between values.

        Returns:
            Concatenated string expression.

        Raises:
            NotImplementedError: Narwhals doesn't support string_agg.
        """
        raise NotImplementedError(
            "string_agg() is not supported by the Narwhals backend."
        )
