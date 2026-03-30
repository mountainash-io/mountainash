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
    from mountainash.core.types import IbisNumericColumnExpr
    from mountainash.expressions.types import IbisExpr

class SubstraitIbisAggregateArithmeticExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitAggregateArithmeticExpressionSystemProtocol["IbisNumericColumnExpr"]
):
    """Ibis implementation of SubstraitAggregateArithmeticExpressionSystemProtocol.

    Implements arithmetic aggregation methods.
    """

    def sum(self, x: IbisNumericColumnExpr, /) -> IbisNumericColumnExpr:
        """Sum values.

        Args:
            x: Expression to sum.

        Returns:
            Sum expression.
        """
        return x.sum()

    def sum0(
        self,
        x: IbisNumericColumnExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericColumnExpr:
        """Sum a set of values. Returns zero for empty set.

        Args:
            x: Expression to sum.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Sum expression (0 for empty).
        """
        return x.sum().fill_null(ibis.literal(0))


    def avg(
        self,
        x: IbisNumericColumnExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericColumnExpr:
        """Average a set of values.

        Args:
            x: Expression to average.
            overflow: Overflow handling (ignored in Ibis).

        Returns:
            Average expression.
        """
        return x.mean()


    def min(self, x: IbisNumericColumnExpr, /) -> IbisNumericColumnExpr:
        """Get minimum value.

        Args:
            x: Expression to find minimum.

        Returns:
            Min expression.
        """
        return x.min()

    def max(self, x: IbisNumericColumnExpr, /) -> IbisNumericColumnExpr:
        """Get maximum value.

        Args:
            x: Expression to find maximum.

        Returns:
            Max expression.
        """
        return x.max()


    def product(
        self,
        x: IbisNumericColumnExpr,
        /,
        overflow: Any = None,
    ) -> IbisNumericColumnExpr:
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
    ) -> IbisNumericColumnExpr:
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
    ) -> IbisNumericColumnExpr:
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
    ) -> IbisNumericColumnExpr:
        """Calculate Pearson correlation coefficient.

        Args:
            x: First expression.
            y: Second expression.
            rounding: Rounding mode (ignored).

        Returns:
            Correlation coefficient.
        """
        return x.corr(y)

    def mode(self, x: IbisNumericColumnExpr, /) -> IbisNumericColumnExpr:
        """Calculate mode (most frequent value).

        Args:
            x: Expression to find mode.

        Returns:
            Mode expression.
        """
        return x.mode()


    def median(self, x: IbisNumericColumnExpr, /) -> IbisNumericColumnExpr:
        """Calculate median.

        Args:
            x: Expression to calculate median.

        Returns:
            Median expression.
        """
        return x.median()


    def quantile(
        self,
        x: IbisNumericColumnExpr,
        /,
        q: float = 0.5,
        interpolation: str = "linear",
    ) -> IbisNumericColumnExpr:
        """Calculate quantile.

        Args:
            x: Expression to calculate quantile.
            q: Quantile value (0-1).
            interpolation: Interpolation method.

        Returns:
            Quantile expression.
        """
        return x.quantile(q)

    # def first(self, x: IbisNumericColumnExpr, /) -> IbisNumericColumnExpr:
    #     """Get first value.

    #     Args:
    #         x: Expression to get first value.

    #     Returns:
    #         First value expression.
    #     """
    #     return x.first()

    # def last(self, x: IbisNumericColumnExpr, /) -> IbisNumericColumnExpr:
    #     """Get last value.

    #     Args:
    #         x: Expression to get last value.

    #     Returns:
    #         Last value expression.
    #     """
    #     return x.last()

    # def n_unique(self, x: IbisNumericColumnExpr, /) -> IbisNumericColumnExpr:
    #     """Count unique values.

    #     Args:
    #         x: Expression to count unique values.

    #     Returns:
    #         Unique count expression.
    #     """
    #     return x.nunique()

    # =========================================================================
    # Substrait Aggregate Arithmetic Methods
    # =========================================================================
