"""Ibis MountainashNullExpressionProtocol implementation.

Implements null handling extensions for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshNullExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr



class MountainAshIbisNullExpressionSystem(IbisBaseExpressionSystem, MountainAshNullExpressionSystemProtocol):
    """Ibis implementation of MountainashNullExpressionProtocol.

    Implements null handling extension methods:
    - fill_null: Replace NULL values with a specified value
    - null_if: Replace values equal to a specified value with NULL
    """

    def fill_null(
        self,
        input: IbisExpr,
        replacement: Any,
        /,
    ) -> IbisExpr:
        """Replace NULL values with the specified replacement value.

        Args:
            input: Expression that may contain NULL values.
            replacement: Value to use in place of NULLs.

        Returns:
            Expression with NULLs replaced by the replacement value.
        """
        return input.fill_null(replacement)
