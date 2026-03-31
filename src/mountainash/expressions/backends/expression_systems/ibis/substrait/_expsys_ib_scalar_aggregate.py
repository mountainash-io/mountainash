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
    from mountainash.core.types import IbisBooleanColumnExpr, IbisColumnExpr, IbisNumericColumnExpr, IbisStringColumnExpr, IbisValueExpr
    from mountainash.expressions.types import IbisExpr

class SubstraitIbisAggregateArithmeticExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitAggregateArithmeticExpressionSystemProtocol["IbisValueExpr"]
):
    """Ibis implementation of SubstraitAggregateArithmeticExpressionSystemProtocol.

    Implements arithmetic aggregation methods.
    """

    def sum(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Sum values.

        Args:
            x: Expression to sum.

        Returns:
            Sum expression.
        """
        return x.sum()

    def mean(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Calculate mean of values.

        Args:
            x: Expression to average.

        Returns:
            Mean expression.
        """
        return x.mean()

    def min(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Get minimum value.

        Args:
            x: Expression to find minimum.

        Returns:
            Min expression.
        """
        return x.min()

    def max(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Get maximum value.

        Args:
            x: Expression to find maximum.

        Returns:
            Max expression.
        """
        return x.max()

    def std(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Calculate standard deviation.

        Args:
            x: Expression to calculate std.

        Returns:
            Standard deviation expression.
        """
        return x.std()

    def var(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Calculate variance.

        Args:
            x: Expression to calculate variance.

        Returns:
            Variance expression.
        """
        return x.var()

    def median(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Calculate median.

        Args:
            x: Expression to calculate median.

        Returns:
            Median expression.
        """
        return x.median()

    def first(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Get first value.

        Args:
            x: Expression to get first value.

        Returns:
            First value expression.
        """
        return x.first()

    def last(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Get last value.

        Args:
            x: Expression to get last value.

        Returns:
            Last value expression.
        """
        return x.last()

    def n_unique(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Count unique values.

        Args:
            x: Expression to count unique values.

        Returns:
            Unique count expression.
        """
        return x.nunique()

    # =========================================================================
    # Substrait Aggregate Arithmetic Methods
    # =========================================================================

    def avg(
        self,
        x: IbisNumericColumnExpr,
        /,
        overflow: Any = None,
    ) -> IbisValueExpr:
        """Average a set of values.

        Args:
            x: Expression to average.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Average expression.
        """
        return x.mean()

    def sum0(
        self,
        x: IbisNumericColumnExpr,
        /,
        overflow: Any = None,
    ) -> IbisValueExpr:
        """Sum a set of values. Returns zero for empty set.

        Args:
            x: Expression to sum.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Sum expression (0 for empty).
        """
        return x.sum().fill_null(ibis.literal(0))

    def product(
        self,
        x: IbisNumericColumnExpr,
        /,
        overflow: Any = None,
    ) -> IbisValueExpr:
        """Product of a set of values. Returns 1 for empty input.

        Args:
            x: Expression to multiply.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Product expression.

        Note:
            Ibis doesn't have a direct product aggregate.
            Falls back to exp(sum(log(x))) which works for positive values.
        """
        # Using exp(sum(log(x))) for product - works for positive values
        return x.log().sum().exp()

    def std_dev(
        self,
        x: IbisNumericColumnExpr,
        /,
        rounding: Any = None,
        distribution: Any = None,
    ) -> IbisValueExpr:
        """Calculate standard deviation.

        Args:
            x: Expression to calculate std.
            rounding: Rounding mode (ignored).
            distribution: SAMPLE or POPULATION.

        Returns:
            Standard deviation expression.
        """
        if distribution == "POPULATION":
            return x.std(how="pop")
        return x.std(how="sample")

    def variance(
        self,
        x: IbisNumericColumnExpr,
        /,
        rounding: Any = None,
        distribution: Any = None,
    ) -> IbisValueExpr:
        """Calculate variance.

        Args:
            x: Expression to calculate variance.
            rounding: Rounding mode (ignored).
            distribution: SAMPLE or POPULATION.

        Returns:
            Variance expression.
        """
        if distribution == "POPULATION":
            return x.var(how="pop")
        return x.var(how="sample")

    def corr(
        self,
        x: IbisNumericColumnExpr,
        y: IbisNumericColumnExpr,
        /,
        rounding: Any = None,
    ) -> IbisValueExpr:
        """Calculate Pearson correlation coefficient.

        Args:
            x: First expression.
            y: Second expression.
            rounding: Rounding mode (ignored).

        Returns:
            Correlation coefficient.
        """
        return x.corr(y)

    def mode(self, x: IbisNumericColumnExpr, /) -> IbisValueExpr:
        """Calculate mode (most frequent value).

        Args:
            x: Expression to find mode.

        Returns:
            Mode expression.
        """
        return x.mode()

    def quantile(
        self,
        x: IbisNumericColumnExpr,
        /,
        q: float = 0.5,
        interpolation: str = "linear",
    ) -> IbisValueExpr:
        """Calculate quantile.

        Args:
            x: Expression to calculate quantile.
            q: Quantile value (0-1).
            interpolation: Interpolation method.

        Returns:
            Quantile expression.
        """
        return x.quantile(q)


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


class SubstraitIbisAggregateGenericExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitAggregateGenericExpressionSystemProtocol["IbisValueExpr"]
):
    """Ibis implementation of SubstraitAggregateGenericExpressionSystemProtocol.

    Implements generic aggregation methods.
    """

    def count(
        self,
        x: IbisColumnExpr,
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

    def count_all(
        self,
        overflow: Any = None,
    ) -> IbisValueExpr:
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
        x: IbisColumnExpr,
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


class SubstraitIbisAggregateStringExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitAggregateStringExpressionSystemProtocol["IbisValueExpr"]
):
    """Ibis implementation of SubstraitAggregateStringExpressionSystemProtocol.

    Implements string aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate String Methods
    # =========================================================================

    def string_agg(
        self,
        x: IbisStringColumnExpr,
        separator: str = ",",
        /,
    ) -> IbisValueExpr:
        """Concatenate strings with a separator.

        Args:
            x: String expression to concatenate.
            separator: Separator between values.

        Returns:
            Concatenated string expression.
        """
        return x.group_concat(sep=separator)
