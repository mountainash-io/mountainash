"""Ibis ScalarAggregateExpressionProtocol implementation.

Implements aggregation operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarAggregateExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr

class SubstraitIbisScalarAggregateExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarAggregateExpressionSystemProtocol):
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

    # =========================================================================
    # Substrait Aggregate Arithmetic Methods
    # =========================================================================

    def avg(
        self,
        x: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
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
        x: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
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
        x: IbisExpr,
        /,
        overflow: Any = None,
    ) -> IbisExpr:
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
        x: IbisExpr,
        /,
        rounding: Any = None,
        distribution: Any = None,
    ) -> IbisExpr:
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
        x: IbisExpr,
        /,
        rounding: Any = None,
        distribution: Any = None,
    ) -> IbisExpr:
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
        x: IbisExpr,
        y: IbisExpr,
        /,
        rounding: Any = None,
    ) -> IbisExpr:
        """Calculate Pearson correlation coefficient.

        Args:
            x: First expression.
            y: Second expression.
            rounding: Rounding mode (ignored).

        Returns:
            Correlation coefficient.
        """
        return x.corr(y)

    def mode(self, x: IbisExpr, /) -> IbisExpr:
        """Calculate mode (most frequent value).

        Args:
            x: Expression to find mode.

        Returns:
            Mode expression.
        """
        return x.mode()

    def quantile(
        self,
        x: IbisExpr,
        /,
        q: float = 0.5,
        interpolation: str = "linear",
    ) -> IbisExpr:
        """Calculate quantile.

        Args:
            x: Expression to calculate quantile.
            q: Quantile value (0-1).
            interpolation: Interpolation method.

        Returns:
            Quantile expression.
        """
        return x.quantile(q)

    # =========================================================================
    # Substrait Aggregate Boolean Methods
    # =========================================================================

    def bool_and(self, x: IbisExpr, /) -> IbisExpr:
        """Aggregate AND - true if all values are true.

        Returns false if any value is false.
        Returns null if input is empty or only contains nulls.

        Args:
            x: Boolean expression to aggregate.

        Returns:
            Aggregated boolean expression.
        """
        return x.all()

    def bool_or(self, x: IbisExpr, /) -> IbisExpr:
        """Aggregate OR - true if any value is true.

        Returns true if any value is true.
        Returns null if input is empty or only contains nulls.

        Args:
            x: Boolean expression to aggregate.

        Returns:
            Aggregated boolean expression.
        """
        return x.any()

    # =========================================================================
    # Substrait Aggregate String Methods
    # =========================================================================

    def string_agg(
        self,
        x: IbisExpr,
        separator: str = ",",
        /,
    ) -> IbisExpr:
        """Concatenate strings with a separator.

        Args:
            x: String expression to concatenate.
            separator: Separator between values.

        Returns:
            Concatenated string expression.
        """
        return x.group_concat(sep=separator)
