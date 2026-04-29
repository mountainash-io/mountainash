"""Ibis implementation of mountainash extension aggregate operations."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainashExtensionAggregateExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


class MountainAshIbisScalarAggregateExpressionSystem(
    IbisBaseExpressionSystem,
    MountainashExtensionAggregateExpressionSystemProtocol["IbisValueExpr"],
):
    """Ibis implementation of mountainash aggregate extensions."""

    def n_unique(self, x: IbisValueExpr, /) -> IbisValueExpr:
        """Count distinct values."""
        return x.nunique()
