"""Polars ScalarComparisonExpressionProtocol implementation.

Implements comparison operations for the Polars backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarComparisonExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr


class PolarsScalarComparisonExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarComparisonExpressionSystemProtocol):
    """Polars implementation of ScalarComparisonExpressionProtocol.

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

    def equal(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        """Whether two values are equal.

        Returns null if either x or y is null.
        """
        return x.eq(y)

    def not_equal(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        """Whether two values are not equal.

        Returns null if either x or y is null.
        """
        return x.ne(y)

    # =========================================================================
    # Ordering Operations
    # =========================================================================

    def lt(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        """Less than comparison.

        Returns null if either x or y is null.
        """
        return x.lt(y)

    def gt(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        """Greater than comparison.

        Returns null if either x or y is null.
        """
        return x.gt(y)

    def lte(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        """Less than or equal comparison.

        Returns null if either x or y is null.
        """
        return x.le(y)

    def gte(self, x: PolarsExpr, y: PolarsExpr, /) -> PolarsExpr:
        """Greater than or equal comparison.

        Returns null if either x or y is null.
        """
        return x.ge(y)

    def between(
        self,
        x: PolarsExpr,
        low: PolarsExpr,
        high: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Whether x is between low and high (inclusive).

        Returns null if any of x, low, or high is null.
        """
        return x.is_between(low, high, closed="both")

    # =========================================================================
    # Boolean Check Operations
    # =========================================================================

    def is_true(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is true.

        Returns false for null values.
        """
        return x.eq(True)

    def is_not_true(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is not true.

        Returns true for null and false values.
        """
        return x.ne(True) | x.is_null()

    def is_false(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is false.

        Returns false for null values.
        """
        return x.eq(False)

    def is_not_false(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is not false.

        Returns true for null and true values.
        """
        return x.ne(False) | x.is_null()

    # =========================================================================
    # Null/NaN Check Operations
    # =========================================================================

    def is_null(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is null.

        NaN is not considered null.
        """
        return x.is_null()

    def is_not_null(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is not null.

        NaN is not considered null.
        """
        return x.is_not_null()

    def is_nan(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is NaN.

        Returns null if x is null.
        """
        return x.is_nan()

    def is_finite(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is finite (not infinite and not NaN).

        Returns null if x is null.
        """
        return x.is_finite()

    def is_infinite(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether a value is infinite.

        Returns null if x is null.
        """
        return x.is_infinite()

    # =========================================================================
    # Null Handling Operations
    # =========================================================================

    def nullif(self, x: PolarsExpr, /, y: PolarsExpr) -> PolarsExpr:
        """Return null if x equals y, otherwise return x.

        Equivalent to SQL NULLIF(x, y).
        """
        return pl.when(x.eq(y)).then(pl.lit(None)).otherwise(x)

    def coalesce(self, *args: PolarsExpr) -> PolarsExpr:
        """Return the first non-null argument.

        If all arguments are null, return null.
        """
        return pl.coalesce(*args)

    def least(self, *args: PolarsExpr) -> PolarsExpr:
        """Return the smallest value.

        Returns null if any argument is null.
        """
        return pl.min_horizontal(*args)

    def least_skip_null(self, *args: PolarsExpr) -> PolarsExpr:
        """Return the smallest value, ignoring nulls.

        Returns null only if all arguments are null.
        """
        # Polars min_horizontal already skips nulls by default
        return pl.min_horizontal(*args)

    def greatest(self, *args: PolarsExpr) -> PolarsExpr:
        """Return the largest value.

        Returns null if any argument is null.
        """
        return pl.max_horizontal(*args)

    def greatest_skip_null(self, *args: PolarsExpr) -> PolarsExpr:
        """Return the largest value, ignoring nulls.

        Returns null only if all arguments are null.
        """
        # Polars max_horizontal already skips nulls by default
        return pl.max_horizontal(*args)
