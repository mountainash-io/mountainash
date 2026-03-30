"""Ibis MountainashNullExpressionProtocol implementation.

Implements null handling extensions for the Ibis backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshNullExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr
    from mountainash.expressions.types import IbisExpr



class MountainAshIbisNullExpressionSystem(IbisBaseExpressionSystem, MountainAshNullExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of MountainashNullExpressionProtocol.

    Implements null handling extension methods:
    - fill_null: Replace NULL values with a specified value
    - null_if: Replace values equal to a specified value with NULL
    """

    def fill_null(
        self,
        input: IbisValueExpr,
        replacement: Any,
        /,
    ) -> IbisValueExpr:
        """Replace NULL values with the specified replacement value.

        Args:
            input: Expression that may contain NULL values.
            replacement: Value to use in place of NULLs.

        Returns:
            Expression with NULLs replaced by the replacement value.
        """
        return input.fill_null(replacement)

    def null_if(
        self,
        input: IbisValueExpr,
        condition: Any,
        /,
    ) -> IbisValueExpr:
        """Replace values equal to condition with NULL.

        SQL NULLIF(input, condition) semantics.
        """
        return input.nullif(condition)

    def fill_nan(
        self,
        input: IbisValueExpr,
        replacement: Any,
        /,
    ) -> IbisValueExpr:
        return ibis.ifelse(input.isnan(), replacement, input)
