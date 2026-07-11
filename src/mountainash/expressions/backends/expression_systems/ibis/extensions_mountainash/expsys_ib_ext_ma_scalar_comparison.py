"""Ibis MountainAsh comparison extension implementation.

Implements is_duplicated for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarComparisonExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr


class MountainAshIbisScalarComparisonExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarComparisonExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of MountainAsh comparison extensions."""


    def is_duplicated(self, x: IbisValueExpr, /) -> IbisValueExpr:
        """Whether the value appears more than once in the column.

        Ibis has no native is_duplicated; a per-value window count > 1 is
        the portable idiom.
        """
        import ibis

        return x.count().over(ibis.window(group_by=x)) > 1
