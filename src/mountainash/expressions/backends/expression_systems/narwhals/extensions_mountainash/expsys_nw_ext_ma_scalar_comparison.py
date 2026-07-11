"""Narwhals MountainAsh comparison extension implementation.

Implements is_duplicated for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarComparisonExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class MountainAshNarwhalsScalarComparisonExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarComparisonExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of MountainAsh comparison extensions."""


    def is_duplicated(self, x: NarwhalsExpr, /) -> NarwhalsExpr:
        """Whether the value appears more than once in the column."""
        return x.is_duplicated()
