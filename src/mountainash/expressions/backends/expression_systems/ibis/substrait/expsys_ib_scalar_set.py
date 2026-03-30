"""Ibis ScalarSetExpressionProtocol implementation.

Implements set membership operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional, Any

import ibis
from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarSetExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr
    from mountainash.expressions.types import IbisExpr


class SubstraitIbisScalarSetExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarSetExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of ScalarSetExpressionProtocol.

    Implements set membership operations:
    - index_in: Return 0-indexed position in list, or -1 if not found
    - is_in: Check if value is in set (boolean)
    - is_not_in: Check if value is not in set (boolean)
    """

    def index_in(
        self,
        needle: IbisValueExpr,
        /,
        *haystack: IbisValueExpr
    ) -> IbisValueExpr:
        """Return the 0-indexed position of needle in haystack, or -1 if not found.

        Args:
            needle: Value to search for.
            *haystack: Values to search in.

        Returns:
            0-indexed position, or -1 if not found.
        """
        if not haystack:
            return ibis.literal(-1)

        # Build a chain of when-then conditions
        result = ibis.literal(-1)
        for i, value in enumerate(reversed(haystack)):
            idx = len(haystack) - 1 - i
            result = ibis.ifelse(needle == value, ibis.literal(idx), result)

        return result

    # def is_in(
    #     self,
    #     needle: IbisValueExpr,
    #     /,
    #     *haystack: IbisValueExpr,
    # ) -> IbisValueExpr:
    #     """Check if needle is in haystack.

    #     Args:
    #         needle: Value to search for.
    #         *haystack: Values to search in.

    #     Returns:
    #         Boolean expression.
    #     """
    #     if not haystack:
    #         return ibis.literal(False)

    #     # For simple literal values, use isin
    #     if all(isinstance(v, (int, float, str, bool, type(None))) for v in haystack):
    #         return needle.isin(list(haystack))

    #     # For expression haystack, use OR chain
    #     result = ibis.literal(False)
    #     for value in haystack:
    #         result = result | (needle == value)
    #     return result

    # def is_not_in(
    #     self,
    #     needle: IbisValueExpr,
    #     /,
    #     *haystack: IbisValueExpr,
    # ) -> IbisValueExpr:
    #     """Check if needle is not in haystack.

    #     Args:
    #         needle: Value to search for.
    #         *haystack: Values to search in.

    #     Returns:
    #         Boolean expression.
    #     """
    #     if not haystack:
    #         return ibis.literal(True)

    #     # For simple literal values, use notin
    #     if all(isinstance(v, (int, float, str, bool, type(None))) for v in haystack):
    #         return needle.notin(list(haystack))

    #     # For expression haystack, negate is_in
    #     return ~self.is_in(needle, *haystack)
