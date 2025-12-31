"""Ibis ScalarComparisonExpressionProtocol implementation.

Implements comparison operations for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarComparisonExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr


class SubstraitIbisScalarComparisonExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarComparisonExpressionSystemProtocol):
    """Ibis implementation of ScalarComparisonExpressionProtocol.

    Implements 23 comparison methods organized into categories:
    - Equality: equal, not_equal
    - Ordering: lt, gt, lte, gte, between
    - Boolean checks: is_true, is_not_true, is_false, is_not_false
    - Null checks: is_null, is_not_null, is_nan, is_finite, is_infinite
    - Null handling: nullif, coalesce, least, least_skip_null, greatest, greatest_skip_null
    """

    # =========================================================================
    # Equality Operations
    # =========================================================================

    def equal(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Whether two values are equal.

        Returns null if either x or y is null.
        """
        return x == y

    def not_equal(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Whether two values are not equal.

        Returns null if either x or y is null.
        """
        return x != y

    def is_not_distinct_from(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Whether two values are equal, treating NULL as comparable.

        is_not_distinct_from(null, null) == True
        This differs from equal() where null values do not compare.
        """
        return (x == y).fillna(x.isnull() & y.isnull())

    def is_distinct_from(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Whether two values are not equal, treating NULL as comparable.

        is_distinct_from(null, null) == False
        This differs from not_equal() where null values do not compare.
        """
        return (x != y).fillna(~(x.isnull() & y.isnull()))

    # =========================================================================
    # Ordering Operations
    # =========================================================================

    def lt(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Less than comparison.

        Returns null if either x or y is null.
        """
        return x < y

    def gt(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Greater than comparison.

        Returns null if either x or y is null.
        """
        return x > y

    def lte(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Less than or equal comparison.

        Returns null if either x or y is null.
        """
        return x <= y

    def gte(self, x: IbisExpr, y: IbisExpr, /) -> IbisExpr:
        """Greater than or equal comparison.

        Returns null if either x or y is null.
        """
        return x >= y

    def between(
        self,
        x: IbisExpr,
        low: IbisExpr,
        high: IbisExpr,
        /,
    ) -> IbisExpr:
        """Whether x is between low and high (inclusive).

        Returns null if any of x, low, or high is null.
        """
        return x.between(low, high)

    # =========================================================================
    # Boolean Check Operations
    # =========================================================================

    def is_true(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is true.

        Returns false for null values.
        """
        return x == ibis.literal(True)

    def is_not_true(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is not true.

        Returns true for null and false values.
        """
        return (x != ibis.literal(True)) | x.isnull()

    def is_false(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is false.

        Returns false for null values.
        """
        return x == ibis.literal(False)

    def is_not_false(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is not false.

        Returns true for null and true values.
        """
        return (x != ibis.literal(False)) | x.isnull()

    # =========================================================================
    # Null/NaN Check Operations
    # =========================================================================

    def is_null(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is null.

        NaN is not considered null.
        """
        return x.isnull()

    def is_not_null(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is not null.

        NaN is not considered null.
        """
        return x.notnull()

    def is_nan(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is NaN.

        Returns null if x is null.
        """
        return x.isnan()

    def is_finite(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is finite (not infinite and not NaN).

        Returns null if x is null.
        """
        return ~x.isnan() & ~x.isinf()

    def is_infinite(self, x: IbisExpr, /) -> IbisExpr:
        """Whether a value is infinite.

        Returns null if x is null.
        """
        return x.isinf()

    # =========================================================================
    # Null Handling Operations
    # =========================================================================

    def nullif(self, x: IbisExpr, /, y: IbisExpr) -> IbisExpr:
        """Return null if x equals y, otherwise return x.

        Equivalent to SQL NULLIF(x, y).
        """
        return x.nullif(y)

    def coalesce(self, *args: IbisExpr) -> IbisExpr:
        """Return the first non-null argument.

        If all arguments are null, return null.
        """
        return ibis.coalesce(*args)

    def least(self, *args: IbisExpr) -> IbisExpr:
        """Return the smallest value.

        Returns null if any argument is null.
        """
        return ibis.least(*args)

    def least_skip_null(self, *args: IbisExpr) -> IbisExpr:
        """Return the smallest value, ignoring nulls.

        Returns null only if all arguments are null.
        """
        # Ibis least should skip nulls by default
        return ibis.least(*args)

    def greatest(self, *args: IbisExpr) -> IbisExpr:
        """Return the largest value.

        Returns null if any argument is null.
        """
        return ibis.greatest(*args)

    def greatest_skip_null(self, *args: IbisExpr) -> IbisExpr:
        """Return the largest value, ignoring nulls.

        Returns null only if all arguments are null.
        """
        # Ibis greatest should skip nulls by default
        return ibis.greatest(*args)
