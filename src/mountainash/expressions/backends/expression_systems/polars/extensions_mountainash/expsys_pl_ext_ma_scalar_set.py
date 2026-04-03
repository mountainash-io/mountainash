"""Polars ScalarSetExpressionProtocol implementation.

Implements set membership operations for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarSetExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsScalarSetExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarSetExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of ScalarSetExpressionProtocol.

    Implements set membership operations:
    - index_in: Return 0-indexed position in list, or -1 if not found
    - is_in: Check if value is in set (boolean)
    - is_not_in: Check if value is not in set (boolean)
    """

    def index_in(
        self,
        needle: PolarsExpr,
        /,
        *haystack: PolarsExpr,
    ) -> PolarsExpr:
        """Return the 0-indexed position of needle in haystack, or -1 if not found.

        Args:
            needle: Value to search for.
            *haystack: Values to search in.

        Returns:
            0-indexed position, or -1 if not found.
        """
        # Convert haystack to a list for checking
        # For each position in haystack, check if needle equals that value
        # Return the first matching position, or -1 if none match
        if not haystack:
            return pl.lit(-1)

        # Build a chain of when-then conditions
        result = pl.lit(-1)
        for i, value in enumerate(reversed(haystack)):
            # Reverse order so first match wins
            idx = len(haystack) - 1 - i
            result = pl.when(needle == value).then(pl.lit(idx)).otherwise(result)

        return result

    def is_in(
        self,
        needle: PolarsExpr,
        /,
        *haystack: PolarsExpr,
    ) -> PolarsExpr:
        """Check if needle is in haystack.

        Args:
            needle: Value to search for.
            *haystack: Values to search in.

        Returns:
            Boolean expression.
        """
        if not haystack:
            return pl.lit(False)

        # Use Polars is_in for simple cases
        if all(isinstance(v, (int, float, str, bool, type(None))) for v in haystack):
            return needle.is_in(list(haystack))

        # For expression haystack, use OR chain
        result = pl.lit(False)
        for value in haystack:
            result = result | (needle == value)
        return result

    def is_not_in(
        self,
        needle: PolarsExpr,
        /,
        *haystack: PolarsExpr,
    ) -> PolarsExpr:
        """Check if needle is not in haystack.

        Args:
            needle: Value to search for.
            *haystack: Values to search in.

        Returns:
            Boolean expression.
        """
        return ~self.is_in(needle, *haystack)
