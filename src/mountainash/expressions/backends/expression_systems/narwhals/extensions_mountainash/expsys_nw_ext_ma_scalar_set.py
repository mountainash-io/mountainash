"""Narwhals ScalarSetExpressionProtocol implementation.

Implements set membership operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarSetExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr



class SubstraitNarwhalsScalarSetExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarSetExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of ScalarSetExpressionProtocol.

    Implements set membership operations:
    - index_in: Return 0-indexed position in list, or -1 if not found
    - is_in: Check if value is in set (boolean)
    - is_not_in: Check if value is not in set (boolean)
    """


    def is_in(
        self,
        needle: NarwhalsExpr,
        /,
        *haystack: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Check if needle is in haystack.

        Args:
            needle: Value to search for.
            *haystack: Values to search in.

        Returns:
            Boolean expression.
        """
        if not haystack:
            # nw.lit(False) is a scalar that doesn't broadcast correctly with pandas
            # Use (needle != needle) to get a column-length False expression
            # This also handles NULL correctly (NULL != NULL is NULL/False)
            return needle != needle

        # For simple literal values, use is_in
        if all(isinstance(v, (int, float, str, bool, type(None))) for v in haystack):
            return needle.is_in(list(haystack))

        # For expression haystack, use OR chain
        result = needle != needle  # Start with column-length False
        for value in haystack:
            result = result | (needle == value)
        return result

    def is_not_in(
        self,
        needle: NarwhalsExpr,
        /,
        *haystack: NarwhalsExpr,
    ) -> NarwhalsExpr:
        """Check if needle is not in haystack.

        Args:
            needle: Value to search for.
            *haystack: Values to search in.

        Returns:
            Boolean expression.
        """
        return ~self.is_in(needle, *haystack)
