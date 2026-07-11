"""Polars MountainAsh comparison extension implementation.

Implements is_duplicated for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarComparisonExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class MountainAshPolarsScalarComparisonExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarComparisonExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of MountainAsh comparison extensions."""


    def is_duplicated(self, x: PolarsExpr, /) -> PolarsExpr:
        """Whether the value appears more than once in the column."""
        return x.is_duplicated()
