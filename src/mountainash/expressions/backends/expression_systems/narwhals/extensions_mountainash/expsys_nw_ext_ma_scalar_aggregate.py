"""Narwhals implementation of mountainash extension aggregate operations."""
from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import (
    MountainashExtensionAggregateExpressionSystemProtocol,
)

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class MountainAshNarwhalsScalarAggregateExpressionSystem(
    NarwhalsBaseExpressionSystem,
    MountainashExtensionAggregateExpressionSystemProtocol[nw.Expr],
):
    """Narwhals implementation of mountainash aggregate extensions."""

    def n_unique(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Count distinct values."""
        return x.n_unique()
