"""Ibis aggregate protocol implementations.

Implements aggregation operations for the Ibis backend using split protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateStringExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisStringColumnExpr, IbisValueExpr


class SubstraitIbisAggregateStringExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitAggregateStringExpressionSystemProtocol["IbisValueExpr"]
):
    """Ibis implementation of SubstraitAggregateStringExpressionSystemProtocol.

    Implements string aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate String Methods
    # =========================================================================

    def string_agg(
        self,
        input: IbisStringColumnExpr,
        /,
        separator: str = ",",
    ) -> IbisValueExpr:
        """Concatenate strings with a separator.

        Args:
            x: String expression to concatenate.
            separator: Separator between values.

        Returns:
            Concatenated string expression.
        """
        return input.group_concat(sep=separator)
