"""Narwhals aggregate protocol implementations.

Implements aggregation operations for the Narwhals backend using split protocols.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import (
    SubstraitAggregateArithmeticExpressionSystemProtocol,
    SubstraitAggregateBooleanExpressionSystemProtocol,
    SubstraitAggregateGenericExpressionSystemProtocol,
    SubstraitAggregateStringExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsAggregateStringExpressionSystem(
    NarwhalsBaseExpressionSystem,
    SubstraitAggregateStringExpressionSystemProtocol["nw.Expr"]
):
    """Narwhals implementation of SubstraitAggregateStringExpressionSystemProtocol.

    Implements string aggregation methods.
    """

    # =========================================================================
    # Substrait Aggregate String Methods
    # =========================================================================

    def string_agg(
        self,
        input: NarwhalsExpr,
        /,
        separator: str = ",",
    ) -> NarwhalsExpr:
        """Concatenate strings with a separator.

        Args:
            x: String expression to concatenate.
            separator: Separator between values.

        Returns:
            Concatenated string expression.

        Raises:
            NotImplementedError: Narwhals doesn't support string_agg.
        """
        raise NotImplementedError(
            "string_agg() is not supported by the Narwhals backend."
        )
