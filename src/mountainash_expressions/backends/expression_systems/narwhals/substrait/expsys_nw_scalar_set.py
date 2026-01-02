"""Narwhals ScalarSetExpressionProtocol implementation.

Implements set membership operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional, Any

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarSetExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import NarwhalsExpr



class SubstraitNarwhalsScalarSetExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarSetExpressionSystemProtocol):
    """Narwhals implementation of ScalarSetExpressionProtocol.

    Implements set membership operations:
    - index_in: Return 0-indexed position in list, or -1 if not found
    - is_in: Check if value is in set (boolean)
    - is_not_in: Check if value is not in set (boolean)
    """

    def index_in(
        self,
        needle: NarwhalsExpr,
        /,
        *haystack: NarwhalsExpr
    ) -> NarwhalsExpr:
        """Return the 0-indexed position of needle in haystack, or -1 if not found.

        Args:
            needle: Value to search for.
            *haystack: Values to search in.

        Returns:
            0-indexed position, or -1 if not found.
        """
        if not haystack:
            return nw.lit(-1)

        # Build a chain of when-then conditions
        result = nw.lit(-1)
        for i, value in enumerate(reversed(haystack)):
            idx = len(haystack) - 1 - i
            result = nw.when(needle == value).then(nw.lit(idx)).otherwise(result)

        return result
